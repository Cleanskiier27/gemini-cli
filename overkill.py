Python 3.14.4 (tags/v3.14.4:23116f9, Apr  7 2026, 14:10:54) [MSC v.1944 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.
>>> def _transform_assets(cfg: OverkillConfig) -> None:
...     # Add minification, image optimization, etc.
... 
... def _deploy_to_target(cfg: OverkillConfig) -> None:
...     # Replace with your actual deploy:
...     subprocess.run(["rsync", "-avz", "src/", str(cfg.deploy_target)], check=True)
...     # or: docker push, aws s3 sync, scp, etc.
