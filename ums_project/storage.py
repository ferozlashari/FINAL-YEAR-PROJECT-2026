from django.contrib.staticfiles.storage import StaticFilesStorage
from whitenoise.storage import CompressedManifestStaticFilesStorage


class ForgivingManifestStorage(CompressedManifestStaticFilesStorage):
    """Cache-busted static files, but a missing manifest entry or a missing file
    returns the plain URL instead of crashing the whole page. Used on serverless
    hosts, where the build output and the running function may not share files."""
    manifest_strict = False

    def url(self, name, force=False):
        try:
            return super().url(name, force)
        except ValueError:
            return StaticFilesStorage.url(self, name)
