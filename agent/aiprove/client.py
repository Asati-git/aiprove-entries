"""AIProve bounty arena client.

Authenticates with an EVM keypair (EIP-191 personal_sign over a server
challenge), then lists / enters / submits to bounties on https://aiprove.fun.

See https://aiprove.fun/skill.md for the official API description.
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any, Optional

import requests
from eth_account import Account
from eth_account.messages import encode_defunct

log = logging.getLogger("aiprove")


class AIProveError(RuntimeError):
    pass


class AIProveClient:
    """Thin REST client for the AIProve bounty board.

    dry_run=True performs every GET (and auth) for real but never POSTs
    enter/submit; it prints the payload it *would* send instead.
    """

    def __init__(
        self,
        private_key: str,
        api_base: str = "https://aiprove.fun",
        handle: Optional[str] = None,
        dry_run: bool = False,
        timeout: int = 30,
        proxies: Optional[dict] = None,
        user_agent: str = "aiprove-client/1.0",
    ) -> None:
        self.api_base = api_base.rstrip("/")
        self.handle = handle
        self.dry_run = dry_run
        self.timeout = timeout
        self.proxies = proxies
        self.session = requests.Session()
        self.session.headers["user-agent"] = user_agent
        if proxies:
            self.session.proxies.update(proxies)

        self.account = Account.from_key(private_key)
        self.address = self.account.address
        self.token: Optional[str] = None

    # ------------------------------------------------------------------ http
    def _get(self, path: str, params: Optional[dict] = None, auth: bool = False) -> Any:
        url = self.api_base + path
        headers = {}
        if auth:
            if not self.token:
                self.authenticate()
            headers["authorization"] = f"Bearer {self.token}"
        r = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
        if r.status_code >= 400:
            raise AIProveError(f"GET {url} -> {r.status_code}: {r.text[:300]}")
        return r.json()

    def _post(self, path: str, body: dict, auth: bool = True) -> Any:
        url = self.api_base + path
        headers = {"content-type": "application/json"}
        if auth:
            if not self.token:
                self.authenticate()
            headers["authorization"] = f"Bearer {self.token}"
        payload = dict(body)
        if self.handle and "handle" not in payload:
            payload["handle"] = self.handle
        if self.dry_run:
            log.info("[dry-run] POST %s %s", url, json.dumps(payload, ensure_ascii=False)[:600])
            return {"dryRun": True, "url": url, "payload": payload}
        r = self.session.post(url, json=payload, headers=headers, timeout=self.timeout)
        if r.status_code >= 400:
            raise AIProveError(f"POST {url} -> {r.status_code}: {r.text[:300]}")
        return r.json()

    # ------------------------------------------------------------------ auth
    def authenticate(self) -> str:
        """Keypair challenge -> EIP-191 signature -> bearer session token."""
        ch = self._get("/api/auth/challenge", params={"address": self.address})
        challenge = ch.get("challenge") if isinstance(ch, dict) else None
        if not challenge:
            raise AIProveError(f"no challenge in response: {ch}")
        signed = Account.sign_message(encode_defunct(text=challenge), self.account.key)
        sig = signed.signature.hex()
        if not sig.startswith("0x"):
            sig = "0x" + sig  # ethers-style, what the server expects
        r = self.session.post(
            self.api_base + "/api/auth/verify",
            json={"address": self.address, "signature": sig},
            headers={"content-type": "application/json"},
            timeout=self.timeout,
        )
        if r.status_code >= 400:
            raise AIProveError(f"auth verify -> {r.status_code}: {r.text[:300]}")
        data = r.json()
        token = data.get("token")
        if not token:
            raise AIProveError(f"no token in verify response: {data}")
        self.token = token
        log.info("authenticated as %s (token expires %s)", self.address, data.get("expiresAt"))
        return token

    # --------------------------------------------------------------- bounties
    def bounties(self, **filters) -> list[dict]:
        data = self._get("/api/bounties", params=filters or None)
        return data.get("bounties", data) if isinstance(data, dict) else data

    def bounty(self, slug: str) -> dict:
        return self._get(f"/api/bounties/{slug}")

    def enter(self, slug: str) -> dict:
        return self._post(f"/api/bounties/{slug}/enter", {})

    # -------------------------------------------------------------- submissions
    def submit_code(self, slug: str, repo_url: str, commit: str, transcript: str) -> dict:
        """Shape A: repo @ commit + build transcript (provenance)."""
        return self._post(
            f"/api/bounties/{slug}/submit",
            {"repoUrl": repo_url, "commit": commit, "transcript": transcript},
        )

    def submit_prediction(self, slug: str, prediction: str) -> dict:
        """Shape B: forecast payload as a string, exactly like the web UI sends it.

        Examples: "yes 0.72", "no 0.6", "452.80", "long", "short".
        """
        return self._post(f"/api/bounties/{slug}/submit", {"prediction": prediction})

    def submit_bughunt(self, slug: str, bugs: list[dict]) -> dict:
        """Bug-hunt payload: JSON list of {fn, input, expected}."""
        return self._post(f"/api/bounties/{slug}/submit", {"prediction": json.dumps(bugs)})

    # ------------------------------------------------------------------- misc
    def me(self) -> dict:
        return self._get("/api/me", auth=True)

    def my_submissions(self) -> dict:
        return self._get("/api/me/submissions", auth=True)

    def leaderboard(self) -> dict:
        return self._get("/api/leaderboard")


def print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))
