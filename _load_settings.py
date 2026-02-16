import json

settings_file : str = "settings.json"
with open(settings_file,mode="r",encoding="utf-8") as f:
    _settings = json.load(f)