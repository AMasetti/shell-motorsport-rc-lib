import pytest
from shell_motorsport import ShellMotorsportCar

@pytest.fixture
def car():
    return ShellMotorsportCar()
