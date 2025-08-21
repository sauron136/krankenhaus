from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.http import Http404
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """Custom exception handler for DRF"""
    
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Now add the custom handling
    if response is not None:
        custom_response_data = {
            'error': True,
            'message': 'An error occurred',
            'details': response.data,
            'status_code': response.status_code
        }
        
        # Handle different types of errors
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            custom_response_data['message'] = 'Invalid request data'
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            custom_response_data['message'] = 'Authentication required'
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            custom_response_data['message'] = 'Permission denied'
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            custom_response_data['message'] = 'Resource not found'
        elif response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            custom_response_data['message'] = 'Method not allowed'
        elif response.status_code >= 500:
            custom_response_data['message'] = 'Internal server error'
            logger.error(f"Internal server error: {exc}", exc_info=True)
        
        response.data = custom_response_data
    
    # Handle Django validation errors
    elif isinstance(exc, ValidationError):
        response = Response({
            'error': True,
            'message': 'Validation error',
            'details': exc.message_dict if hasattr(exc, 'message_dict') else list(exc.messages),
            'status_code': status.HTTP_400_BAD_REQUEST
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Handle 404 errors
    elif isinstance(exc, Http404):
        response = Response({
            'error': True,
            'message': 'Resource not found',
            'details': {'detail': 'The requested resource was not found.'},
            'status_code': status.HTTP_404_NOT_FOUND
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Handle unexpected errors
    else:
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        response = Response({
            'error': True,
            'message': 'An unexpected error occurred',
            'details': {'detail': 'Please try again later or contact support.'},
            'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return response

