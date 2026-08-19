"""
Standard API response helpers.
"""


class ApiResponse:

    @staticmethod
    def success(
        data=None,
        message: str = "Request successful.",
    ):

        return {
            "success": True,
            "message": message,
            "data": data,
        }

    @staticmethod
    def error(
        message: str,
        data=None,
    ):

        return {
            "success": False,
            "message": message,
            "data": data,
        }