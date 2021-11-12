import ftplib
import logging
import os
import shutil
from os import chdir, listdir
from os.path import isfile, join

_logger = logging.getLogger(__name__)

# pylint: disable=R0201
# pylint: disable=R0913
# pylint: disable=R0902


class Ftp:
    """
    FTP Class and functions
    """

    FTYPE_LIST = ["TEXT", "BINA"]

    def __init__(
        self,
        host,
        username,
        password,
        mode="test",
        archive_remote=False,
        archive_local=False,
    ):

        self.mode = mode
        self.host = host
        self.username = username
        self.password = password
        self.connection = False
        self.state = "Disconnected"
        self.archive_remote = archive_remote
        self.archive_local = archive_local
        self.default_type = "BINA"

        self.connect()

    def set_connection(self, ftp):
        """
        Store connection made
        """
        self.connection = ftp
        self.state = "Connected"

    def clear_connection(self):
        """
        Disconnect connection made
        """

        self.connection = False
        self.state = "Disconnected"

    def connect(self):
        """
        Make a connection
        """
        try:
            ftp = ftplib.FTP(self.host)
            ftp.login(self.username, self.password)
            self.set_connection(ftp)
            return ftp

        except ftplib.error_perm:
            _logger.debug("Error connecting to FTP server.")

    def disconnect(self):
        """
        Disconnect
        """
        self.connection.quit()
        self.clear_connection()

    def download_files(self, srcpath, dstpath, files=False, ftype=False):
        """
        Download files from remote
        """
        if ftype not in self.FTYPE_LIST or ftype is False:
            ftype = self.default_type

        if not self.connection or not srcpath or not dstpath:
            return False

        # switch to export directory to download files from
        self.connection.cwd(srcpath)

        # import all files from the directory
        if not files:
            items = []
            self.connection.retrlines("LIST", items.append)
            files = [" ".join(item.split()[8:]) for item in items if item[0] == "-"]

        # process files
        for _idx, file in enumerate(files):
            host_file = join(dstpath, file)
            remote_file = join(srcpath, file)
            try:
                if ftype == "TEXT":
                    with open(host_file, "w") as local_file:
                        self.connection.retrlines(
                            "RETR " + remote_file,
                            lambda s, w=local_file.write: w(s + "\n"),
                        )
                else:
                    with open(host_file, "wb") as local_file:
                        self.connection.retrbinary(
                            "RETR " + remote_file, local_file.write
                        )

            except ftplib.error_perm:
                _logger.debug("Error downloading files")

        return True

    def delete_remote_files(self, path):
        """
        Delete files on remote folder
        """

        if not self.archive_remote:
            _logger.debug("Archive not set for remote. Cannot delete.")

        files = False

        if not self.connection or not path:
            return False

        # switch to export directory to download files from
        self.connection.cwd(path)

        # import all files from the directory
        if not files:
            items = []
            self.connection.retrlines("LIST", items.append)
            files = [" ".join(item.split()[8:]) for item in items if item[0] == "-"]

        # process files
        for file in files:

            try:
                self.connection.delete(file)
            except ftplib.error_perm:
                _logger.debug("Error deleting files")

        return True

    def archive_local_files(self, src_file_path, archive_file_path):
        """
        Archive files locally after processing
        """

        if not self.archive_local:
            _logger.debug("Archive not set for Local. Cannot Archive.")
            return False

        files = False

        if not self.connection or not src_file_path or not archive_file_path:
            return False

        # import all files from the directory
        if not files:
            files = os.listdir(src_file_path)

        # process files
        for file in files:

            src_file = join(src_file_path, file)

            try:
                shutil.move(src_file, archive_file_path)
            except ftplib.error_perm:
                _logger.debug("Error Moving files")

        return True

    def archive_local_file(self, src_file, archive_file_path):
        """
        Archives a single local file
        """
        try:
            shutil.move(src_file, archive_file_path)
        except ftplib.error_perm:
            _logger.debug("Error Moving files")

        return True

    def upload_files(self, srcpath, dstpath, arcpath=False, files=False, ftype=False):
        """
        Upload files to remote
        """

        if ftype not in self.FTYPE_LIST or ftype is False:
            ftype = self.default_type

        if not self.connection or not srcpath or not dstpath:
            return False

        # switch to local directory to upload files from
        chdir(srcpath)

        # import all files from the directory
        if not files:
            files = [f for f in listdir(srcpath) if isfile(join(srcpath, f))]

        # set directory on remote
        self.connection.cwd(dstpath)

        # process files
        for file in files:
            host_file = join(srcpath, file)

            try:
                if ftype == "TXT":
                    with open(host_file) as local_file:
                        self.connection.storlines("STOR " + file, local_file)
                else:
                    with open(host_file, "rb") as local_file:
                        self.connection.storbinary("STOR " + file, local_file)

                # archive file locally if needed only on exporting from Odoo
                if arcpath and self.archive_local:
                    self.archive_local_file(host_file, arcpath)

            except ftplib.error_perm:
                _logger.debug("Error uploading files")

        return True

    def move_remote_files(self, srcpath, delpath, arcpath, ftype=False):
        """
        Fetch remote files
        Clear them on remote folder
        Copy the files back to remote archive folder
        """

        if ftype not in self.FTYPE_LIST or ftype is False:
            ftype = self.default_type

        if not self.archive_remote:
            _logger.debug("Archive not set for local or remote. Cannot move.")

        if not self.delete_remote_files(delpath):
            _logger.debug("Error deleting remote files")

        if not self.upload_files(srcpath, arcpath, ftype=ftype):
            _logger.debug("Error uploading files")

    def move_local_files(self, dstpath, delpath, arcpath, ftype=False):
        """
        Upload files to remote folder and archive locally
        """
        if ftype not in self.FTYPE_LIST or ftype is False:
            ftype = self.default_type

        if not self.upload_files(delpath, dstpath, arcpath, ftype=ftype):
            _logger.debug("Error uploading files")

        # archive immediately after uploading and don't use this.
        # if not self.archive_local_files(delpath, arcpath):
        #    _logger.debug("Error archiving local files")
