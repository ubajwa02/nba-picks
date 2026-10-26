"""Team-strength model for moneylines, spreads and totals (champion candidate).

Exponentially time-weighted ridge regressions on past results only:
  margin_home = hca + r_home - r_away (+ rest terms)
  points(team vs opp) = base + off_team - def_opp + home_pts*[home] (+ rest terms)
Predictions give the expected margin and total; spreads/totals/moneylines come
from the integer distributions in dist.py with sigmas fitted on explore data.
Everything a prediction uses is strictly before the game's start date.
"""
from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass, field, asdict

import numpy as np

from ..teams import TEAMS
from . import dist

TEAM_IDX = {t: i for i, t in enumerate(sorted(TEAMS))}
NT = len(TEAM_IDX)


@dataclass
class RatingsParams:
    half_life_days: float = 60.0
    max_age_days: float = 420.0
    ridge: float = 4.0            # penalty on team coefficients (in games-equivalent)
    sigma_margin: float = 12.6
    sigma_total: float = 18.5
    rest_features: bool = False   # back-to-back terms (challenger hypothesis)
    total_trend: bool = False     # linear time trend in the points model (league scoring drift)
    # player availability (models/availability.py): margin residual ~ b_m*(home_missing - away_missing),
    # total residual ~ b_t*(home_missing + away_missing), fitted on prior games only and shrunk to 0
    # with the strength of `avail_ridge` games. See the leakage caveat in availability.py.
    availability: bool = False
    avail_ridge: float = 100.0
    min_games: int = 150          # refuse to predict on too little data

    def to_dict(self):
        return asdict(self)


@dataclass
class Game:
    game_id: str
    date: dt.date
    home: str
    away: str
    home_score: int | None = None
    away_score: int | None = None
    home_rest: int | None = None   # days since previous game (1 = back-to-back)
    away_rest: int | None = None
    home_missing: float = 0.0      # value of absent regulars (models/availability.py)
    away_missing: float = 0.0
    avail_known: bool = False      # False: no box score / too few team games; feature is 0


def add_rest_days(games: list[Game]) -> None:
    last: dict[str, dt.date] = {}
    for g in sorted(games, key=lambda g: (g.date, g.game_id)):
        g.home_rest = (g.date - last[g.home]).days if g.home in last else None
        g.away_rest = (g.date - last[g.away]).days if g.away in last else None
        last[g.home] = last[g.away] = g.date


class RatingsModel:
    version = "ratings-v1"

    def __init__(self, params: RatingsParams | None = None):
        self.p = params or RatingsParams()
        self.fitted_on: dt.date | None = None
        self.n_games = 0
        self.avail_m = self.avail_t = 0.0
        self.avail_n = 0

    # ---------------- fitting ----------------
    def fit(self, history: list[Game], as_of: dt.date) -> "RatingsModel":
        p = self.p
        hist = [g for g in history if g.home_score is not None and g.date < as_of
                and (as_of - g.date).days <= p.max_age_days and g.home in TEAM_IDX and g.away in TEAM_IDX]
        self.n_games = len(hist)
        self.fitted_on = as_of
        if len(hist) < p.min_games:
            self.coef_m = self.coef_t = None
            return self
        age = np.array([(as_of - g.date).days for g in hist], float)
        w = np.exp(-math.log(2) * age / p.half_life_days)
        nr = 2 if p.rest_features else 0
        ntr = 1 if p.total_trend else 0
        # margin model
        X = np.zeros((len(hist), 1 + NT + nr)); y = np.zeros(len(hist))
        for i, g in enumerate(hist):
            X[i, 0] = 1
            X[i, 1 + TEAM_IDX[g.home]] = 1
            X[i, 1 + TEAM_IDX[g.away]] = -1
            if nr:
                X[i, 1 + NT] = 1.0 if g.home_rest == 1 else 0.0
                X[i, 2 + NT] = 1.0 if g.away_rest == 1 else 0.0
            y[i] = g.home_score - g.away_score
        pen = np.zeros(X.shape[1]); pen[1:1 + NT] = p.ridge
        self.coef_m = _wridge(X, y, w, pen)
        # points model: one row per team-game
        k = 2 + 2 * NT + nr + ntr
        Xt = np.zeros((2 * len(hist), k)); yt = np.zeros(2 * len(hist)); wt = np.repeat(w, 2)
        for i, g in enumerate(hist):
            for j, (t, o, pts, home, rest) in enumerate(((g.home, g.away, g.home_score, 1, g.home_rest),
                                                          (g.away, g.home, g.away_score, 0, g.away_rest))):
                r = 2 * i + j
                Xt[r, 0] = 1; Xt[r, 1] = home
                Xt[r, 2 + TEAM_IDX[t]] = 1; Xt[r, 2 + NT + TEAM_IDX[o]] = -1
                if nr:
                    Xt[r, 2 + 2 * NT] = 1.0 if rest == 1 else 0.0
                    Xt[r, 3 + 2 * NT] = 1.0 if (g.away_rest if home else g.home_rest) == 1 else 0.0
                if ntr:
                    # 0 at the most recent game, so the intercept is the latest level. Anchoring at
                    # as_of extrapolated the trend across the off-season (opening night 2026-27:
                    # expected total 210 vs a league average of 230).
                    Xt[r, k - 1] = -(age[i] - age.min()) / 365.0
                yt[r] = pts
        pent = np.zeros(k); pent[2:2 + 2 * NT] = p.ridge
        self.coef_t = _wridge(Xt, yt, wt, pent)
        self.avail_m = self.avail_t = 0.0; self.avail_n = 0
        if p.availability:
            self._fit_availability(hist, w, X, y, Xt, yt)
        return self

    def _fit_availability(self, hist, w, X, y, Xt, yt) -> None:
        """Second stage, on the fit window only: regress the rating model's margin residual on
        home_missing - away_missing and its total residual on home_missing + away_missing.
        Games without the feature (no box score) are left out. Ridge shrinkage toward 0 with the
        weight of `avail_ridge` games of typical feature size: b = Sxr / (Sxx * (1 + ridge / Sw))."""
        known = np.array([bool(getattr(g, "avail_known", False)) for g in hist])
        self.avail_n = int(known.sum())
        if self.avail_n < 30:
            return
        hm = np.array([float(getattr(g, "home_missing", 0.0) or 0.0) for g in hist])
        am = np.array([float(getattr(g, "away_missing", 0.0) or 0.0) for g in hist])
        rm = y - X @ self.coef_m
        pt = Xt @ self.coef_t
        rt = (yt[0::2] + yt[1::2]) - (pt[0::2] + pt[1::2])
        wk = w[known]; sw = wk.sum()
        for attr, x, r in (("avail_m", hm - am, rm), ("avail_t", hm + am, rt)):
            xk, rk = x[known], r[known]
            sxx = float((wk * xk * xk).sum())
            if sxx <= 0:
                continue
            setattr(self, attr, float((wk * xk * rk).sum()) / (sxx * (1.0 + self.p.avail_ridge / sw)))

    # ---------------- prediction ----------------
    def ready(self) -> bool:
        return getattr(self, "coef_m", None) is not None

    def predict(self, home: str, away: str, home_rest: int | None = None, away_rest: int | None = None,
                home_missing: float = 0.0, away_missing: float = 0.0) -> dict:
        if not self.ready():
            raise RuntimeError(f"model not fitted (only {self.n_games} games)")
        p = self.p; c = self.coef_m; ct = self.coef_t
        hb, ab = float(home_rest == 1), float(away_rest == 1)
        mu_m = c[0] + c[1 + TEAM_IDX[home]] - c[1 + TEAM_IDX[away]]
        if p.rest_features:
            mu_m += c[1 + NT] * hb + c[2 + NT] * ab
        def pts(t, o, home_flag, own_b2b, opp_b2b):
            v = ct[0] + ct[1] * home_flag + ct[2 + TEAM_IDX[t]] - ct[2 + NT + TEAM_IDX[o]]
            if p.rest_features:
                v += ct[2 + 2 * NT] * own_b2b + ct[3 + 2 * NT] * opp_b2b
            return v
        mu_t = pts(home, away, 1, hb, ab) + pts(away, home, 0, ab, hb)
        out = dict(mu_margin=float(mu_m), sigma_margin=p.sigma_margin, mu_total=float(mu_t),
                   sigma_total=p.sigma_total, n_games=self.n_games, hca=float(c[0]))
        if p.availability:
            hm, am = float(home_missing or 0.0), float(away_missing or 0.0)
            adj_m, adj_t = self.avail_m * (hm - am), self.avail_t * (hm + am)
            out["mu_margin"] += adj_m; out["mu_total"] += adj_t
            out["availability_adj"] = dict(margin=adj_m, total=adj_t, coef_margin=self.avail_m,
                                           coef_total=self.avail_t, n_fit=self.avail_n)
        return out

    def ratings(self) -> dict[str, float]:
        return {t: float(self.coef_m[1 + i]) for t, i in TEAM_IDX.items()} if self.ready() else {}

    # market probabilities from a prediction
    @staticmethod
    def prob(pred: dict, market: str, selection: str, line: float | None) -> tuple[float, float]:
        if market == "ml":
            return dist.ml_prob(pred["mu_margin"], pred["sigma_margin"], selection), 0.0
        if market == "spread":
            return dist.margin_probs(pred["mu_margin"], pred["sigma_margin"], line, selection)
        if market == "total":
            return dist.total_probs(pred["mu_total"], pred["sigma_total"], line, selection)
        raise ValueError(market)


def _wridge(X, y, w, pen):
    sw = np.sqrt(w)
    A = X * sw[:, None]; b = y * sw
    return np.linalg.solve(A.T @ A + np.diag(pen) + 1e-9 * np.eye(X.shape[1]), A.T @ b)
