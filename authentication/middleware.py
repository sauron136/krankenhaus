from django.contrib.auth.models import AnonymousUser
from django.utils.deprecation import MiddlewareMixin
from .backends import JWTAuthenticationBackend

class JWTAuthenticationMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        self.backend = JWTAuthenticationBackend()
        
    def __call__(self, request):
        self.process_request(request)
        response = self.get_response(request)
        return response
    
    def process_request(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            user = self.backend.authenticate(request, token=token)
            
            if user:
                request.user = user
            else:
                request.user = AnonymousUser()
        else:
            request.user = AnonymousUser()
