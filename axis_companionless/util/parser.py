from typing import Union


class ParamObject:
    """A class to represent nested configuration as an object with dynamic attributes."""

    def __setattr__(self, name: str, value: Union[str, "ParamObject"]) -> None:
        """Set an attribute on the object dynamically, ensuring it's a string or nested ParamObject."""
        if isinstance(value, dict):
            value = ParamObject.from_dict(value)
        super().__setattr__(name, value)

    @classmethod
    def from_dict(cls, d: dict) -> "ParamObject":
        """Create a ParamObject from a dictionary."""
        obj = cls()
        for key, value in d.items():
            setattr(obj, key, value)
        return obj

    def __getattr__(self, name: str) -> Union[str, "ParamObject"]:
        """Gets the attribute and ensures it's of type str or nested ParamObject."""
        return super().__getattribute__(name)

    def __repr__(self) -> str:
        """Custom repr to display nested object nicely."""
        return f"{self.__dict__}"


class ParamParser:
    def __init__(self) -> None:
        self.config: dict = {}

    def set_nested_value(self, keys: list[str], value: str) -> None:
        """Sets a value in a nested dictionary given a list of keys."""
        d = self.config
        for key in keys[:-1]:
            if key not in d:
                d[key] = {}
            d = d[key]
        d[keys[-1]] = value

    def parse_from_string(self, config_string: str) -> ParamObject:
        """Parses a configuration string into a nested ParamObject."""
        lines = config_string.strip().splitlines()
        for line in lines:
            line = line.strip()
            if line and "=" in line:
                key, value = line.split("=", 1)
                keys = key.split(".")
                self.set_nested_value(keys, value)
        return ParamObject.from_dict(self.config)
