"""Shell Motorsport RC Car control library."""
try:
    from .shell_motorsport import ShellMotorsportCar, Controller
except ImportError:
    # Fallback for direct script execution
    from shell_motorsport import ShellMotorsportCar, Controller

__version__ = "0.2.0"
__all__ = ["ShellMotorsportCar", "Controller"]

