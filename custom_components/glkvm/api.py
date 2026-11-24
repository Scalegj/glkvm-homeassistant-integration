import aiohttp
import pyotp


class GlkvmError(Exception):
    """Something went wrong talking to the KVM."""


class GlkvmAuthError(GlkvmError):
    """The username or password was rejected."""


class GlkvmSslError(GlkvmError):
    """The KVM's certificate failed verification."""


def _describe_error(path, status, payload):
    result = payload.get("result") if isinstance(payload, dict) else None
    if isinstance(result, dict):
        message = result.get("error_msg") or result.get("error")
        if message:
            return f"{path}: {message}"
    return f"{path} returned HTTP {status}"


class GlkvmClient:
    def __init__(self, host, username, password, session, totp_secret=None):
        self._url = f"https://{host}/api"
        self._session = session
        self._username = username
        self._password = password
        self._totp = pyotp.TOTP(totp_secret) if totp_secret else None

    def _auth_headers(self):
        passwd = self._password
        if self._totp is not None:
            try:
                passwd += self._totp.now()
            except ValueError as err:
                raise GlkvmAuthError("Invalid TOTP secret") from err
        return {"X-KVMD-User": self._username, "X-KVMD-Passwd": passwd}

    async def _request(self, method, path, params=None, form=None, raw=False):
        try:
            return await self._send(method, path, params, form, raw)
        except GlkvmAuthError:
            if self._totp is None:
                raise
            return await self._send(method, path, params, form, raw)

    async def _send(self, method, path, params, form, raw):
        data = None
        if form is not None:
            data = aiohttp.FormData()
            for name, value in form.items():
                data.add_field(name, value, content_type="text/plain")
        try:
            async with self._session.request(
                method,
                f"{self._url}{path}",
                params=params,
                data=data,
                headers=self._auth_headers(),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status in (401, 403):
                    raise GlkvmAuthError("Invalid username or password")
                status = response.status
                try:
                    payload = await response.json(content_type=None)
                except ValueError:
                    payload = None
        except aiohttp.ClientSSLError as err:
            raise GlkvmSslError(f"Certificate verification failed: {err}") from err
        except (aiohttp.ClientError, TimeoutError) as err:
            raise GlkvmError(f"Cannot reach the KVM: {err}") from err
        if raw and status == 200 and payload is not None:
            return payload
        if status != 200 or not isinstance(payload, dict) or not payload.get("ok"):
            if status == 200 and payload is None:
                raise GlkvmError(f"{path} returned invalid JSON")
            raise GlkvmError(_describe_error(path, status, payload))
        return payload["result"]

    async def async_get_2fa_enabled(self):
        result = await self._request("GET", "/2fa/is_enabled")
        return result["enabled"]

    async def async_get_atx(self):
        return await self._request("GET", "/atx")

    async def async_get_info(self):
        return await self._request("GET", "/info", {"fields": "system"})

    async def async_get_version(self):
        return await self._request("GET", "/upgrade/version")

    async def async_set_power(self, action):
        await self._request("POST", "/atx/power", {"action": action})

    async def async_click(self, button):
        await self._request("POST", "/atx/click", {"button": button})

    async def async_get_msd(self):
        return await self._request("GET", "/msd")

    async def async_get_hid(self):
        return await self._request("GET", "/hid")

    async def async_set_jiggler(self, active):
        await self._request(
            "POST", "/hid/set_params", {"jiggler": "true" if active else "false"}
        )

    async def async_set_msd_connected(self, connected):
        await self._request(
            "POST",
            "/msd/set_connected",
            {"connected": "true" if connected else "false"},
        )

    async def async_set_msd_image(self, image):
        await self._request("POST", "/msd/set_params", {"image": image})

    async def async_get_edid_list(self):
        """Return {label: hex} for EDIDs from KVM"""
        items = await self._request("GET", "/upgrade/edid_list", raw=True)
        return {item["label"]: item["content"] for item in items}

    async def async_get_edid(self):
        result = await self._request("GET", "/upgrade/get_edid")
        return result["edid"]

    async def async_set_edid(self, edid):
        await self._request("POST", "/upgrade/edid", form={"edid": edid})
