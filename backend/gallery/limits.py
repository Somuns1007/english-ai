"""Bound multipart bodies before parsing, including chunked uploads without a length."""
from starlette.responses import JSONResponse


class GalleryBodyLimit:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['path'].rstrip('/') != '/api/gallery/upload':
            return await self.app(scope, receive, send)
        limit = 11 * 1024 * 1024  # 10 MiB file plus bounded multipart overhead.
        headers = dict(scope.get('headers', []))
        try:
            length = int(headers.get(b'content-length', b'0'))
        except ValueError:
            return await JSONResponse({'detail': '无效的上传请求。'}, 400)(scope, receive, send)
        if length > limit:
            return await JSONResponse({'detail': '图片不能超过 10MB。'}, 413)(scope, receive, send)
        chunks, total = [], 0
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            total += len(message.get('body', b''))
            if total > limit:
                return await JSONResponse({'detail': '图片不能超过 10MB。'}, 413)(scope, receive, send)
            chunks.append(message)
            if not message.get('more_body', False):
                break
        iterator = iter(chunks)

        async def bounded_receive():
            return next(iterator, {'type': 'http.request', 'body': b'', 'more_body': False})

        await self.app(scope, bounded_receive, send)
