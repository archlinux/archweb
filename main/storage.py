import cssmin
import jsmin

from django.contrib.staticfiles.storage import ManifestStaticFilesStorage
from django.core.files.base import ContentFile
from django.utils.encoding import smart_str


class MinifiedStaticFilesStorage(ManifestStaticFilesStorage):
    """
    A static file system storage backend which minifies the hashed
    copies of the files it saves. It currently knows how to process
    CSS and JS files. Files containing '.min' anywhere in the filename
    are skipped as they are already assumed minified.
    """
    minifiers = (
        ('.css', cssmin.cssmin),
        ('.js', jsmin.jsmin),
    )

    def post_process(self, paths, dry_run=False, **options):
        for original_path, processed_path, processed in super(
                MinifiedStaticFilesStorage, self).post_process(
                paths, dry_run, **options):
            for ext, func in self.minifiers:
                if '.min' in original_path:
                    continue
                if original_path.endswith(ext):
                    with self._open(processed_path) as processed_file:
                        minified = func(processed_file.read().decode('utf-8'))
                    minified_file = ContentFile(smart_str(minified))
                    self.delete(processed_path)
                    self._save(processed_path, minified_file)
                    processed = True

            yield original_path, processed_path, processed
