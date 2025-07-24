from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

class BlueDoveJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # First perform the regular JWT authentication
        auth_response = super().authenticate(request)
        
        # If no authentication was provided or failed, return None
        if auth_response is None:
            return None
            
        user, token = auth_response
        # Check if the user is bluedove
        if user.username != "bluedove":
            raise AuthenticationFailed("Access denied. Only bluedove user is allowed.")
            
        return user, token