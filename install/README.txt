Fathom: per-user install (spec 031)
===================================

Windows:  double-click "Install Fathom.bat"
macOS:    double-click "Install Fathom.command"
Linux:    sh install-fathom.sh

Needs Python 3.11 or newer. Installs for you only: no admin rights, no PATH or
registry changes. With a wheelhouse/ folder beside the installer (an offline
bundle), nothing is downloaded. Without one, pip downloads pandas and PyYAML.

Then open "Fathom" from the Start menu, Desktop, ~/Applications or your
applications menu. Reports are saved in a Fathom folder in your home folder.
Nothing leaves this computer, but reports can contain values from your table:
check them before you share them, and keep them out of cloud-synced folders if
that matters.

Remove it: run the installer again with --uninstall (your reports stay).
Details: docs/install.md in the repository.
