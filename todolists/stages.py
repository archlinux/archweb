from dataclasses import dataclass


@dataclass(frozen=True)
class Stage:
    key: str
    name: str
    description: str
    caption: str
    per_package: bool


# Ordered by the sequence in which the stages appear on a todo list
STAGES = {stage.key: stage for stage in (
    Stage('draft', 'Draft',
          'The todo list is being prepared. Packages can still be added or removed; '
          'nothing has been rebuilt yet.',
          'Start task', per_package=False),
    Stage('rebuild_staging', 'Rebuild in staging',
          'Packages are rebuilt and added to the staging repositories. Mark each '
          'package as complete once it is in staging. When all packages are '
          'complete, they are moved to testing.',
          'Mark as moved to testing', per_package=True),
    Stage('rebuild_testing', 'Rebuild in testing',
          'Packages are rebuilt and added to the testing repositories. Mark each '
          'package as complete once it is in testing. When all packages are '
          'complete, they are moved to the stable repositories.',
          'Mark as moved to stable', per_package=True),
    Stage('test_testing', 'Test in testing',
          'Rebuilt packages are tested in the testing repositories before they are '
          'moved to the stable repositories.',
          'Mark as moved to stable repos', per_package=False),
    Stage('in_progress', 'In progress',
          'Work on this task is in progress. Mark each package as complete when it '
          'is done.',
          'Mark as complete', per_package=True),
)}

# vim: set ts=4 sw=4 et:
