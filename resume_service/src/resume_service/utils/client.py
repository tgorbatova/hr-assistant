from typing import Any

from aiohttp import ClientResponse, ClientSession, ClientTimeout, FormData
from fastapi import UploadFile


class BaseHttpClient:
    def __init__(self, base_url: str = "", timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = ClientTimeout(total=timeout)
        self.session: ClientSession | None = None

    async def __aenter__(self):
        if self.session is None or self.session.closed:
            self.session = ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def close(self):
        """Explicitly close the session if needed"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: dict[str, Any] = None,
        data: Any = None,
        json: Any = None,
        file: UploadFile = None,
        headers: dict[str, str] = None,
    ) -> ClientResponse | str | bytes:
        if not self.session or self.session.closed:
            raise RuntimeError("Session is not started. Use 'async with BaseHttpClient(...)'")

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        async with self.session.request(
            method=method.upper(), url=url, params=params, data=data, json=json, headers=headers
        ) as response:
            response.raise_for_status()  # Raises exception for 4xx or 5xx
            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return await response.json()
            if "text" in content_type:
                return await response.text()
            # Assume it's a file or binary stream
            return await response.read()

    async def get(self, endpoint: str, **kwargs) -> Any:
        return await self._request("GET", endpoint, **kwargs)

    async def post(
        self,
        endpoint: str,
        *,
        files: UploadFile | list[UploadFile] | list[tuple[str, UploadFile]] | None = None,
        data: dict[str, Any] | None = None,
        json: Any = None,
        params: dict[str, Any] = None,
        headers: dict[str, str] = None,
    ) -> Any:
        """POST request with optional file upload support.

        Args:
            endpoint: API endpoint
            files: Single UploadFile, list of UploadFiles, or list of (field_name, UploadFile)
            data: Form data fields
            json: JSON payload (ignored if files are provided)
            params: URL query parameters
            headers: Request headers

        """
        form = None

        if files:
            form = FormData()

            # Normalize input to List[Tuple[str, UploadFile]]
            if isinstance(files, UploadFile):
                files = [("file", files)]
            elif isinstance(files, list):
                if all(isinstance(f, UploadFile) for f in files):
                    files = [("file", f) for f in files]
                elif all(isinstance(f, tuple) and isinstance(f[1], UploadFile) for f in files):
                    pass
                else:
                    raise ValueError(
                        "Invalid format for 'files'. Must be UploadFile, list of UploadFiles, or list of (field_name, UploadFile)"
                    )

            for field_name, file in files:
                file_content = await file.read()
                file.file.seek(0)  # allow FastAPI to reuse it if needed
                form.add_field(
                    name=field_name,
                    value=file_content,
                    filename=file.filename,
                    content_type=file.content_type or "application/octet-stream",
                )

            # Add additional form fields
            if data:
                for key, value in data.items():
                    form.add_field(name=key, value=str(value))

        return await self._request(
            "POST", endpoint, params=params, data=form or data, json=None if form else json, headers=headers
        )

    async def put(self, endpoint: str, **kwargs) -> Any:
        return await self._request("PUT", endpoint, **kwargs)

    async def delete(self, endpoint: str, **kwargs) -> Any:
        return await self._request("DELETE", endpoint, **kwargs)

    async def patch(self, endpoint: str, **kwargs) -> Any:
        return await self._request("PATCH", endpoint, **kwargs)
