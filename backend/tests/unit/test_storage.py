"""Tests for R2/S3-compatible storage service."""

from unittest.mock import MagicMock, patch
import pytest
from botocore.exceptions import ClientError

from app.services import storage


def _make_client_error(code: str = "NoSuchKey", message: str = "Not Found"):
    """Helper to construct a botocore ClientError."""
    return ClientError(
        error_response={"Error": {"Code": code, "Message": message}},
        operation_name="TestOp",
    )


# ---------------------------------------------------------------------------
# _get_s3_client
# ---------------------------------------------------------------------------


class TestGetS3Client:
    """Tests for _get_s3_client."""

    @patch.object(storage, "boto3")
    @patch.object(storage, "settings")
    def test_returns_client_when_r2_configured(self, mock_settings, mock_boto3):
        mock_settings.R2_ENDPOINT_URL = "https://r2.example.com"
        mock_settings.R2_ACCESS_KEY_ID = "key-id"
        mock_settings.R2_SECRET_ACCESS_KEY = "secret-key"

        client = storage._get_s3_client()

        mock_boto3.client.assert_called_once_with(
            "s3",
            endpoint_url="https://r2.example.com",
            aws_access_key_id="key-id",
            aws_secret_access_key="secret-key",
        )
        assert client is mock_boto3.client.return_value

    @patch.object(storage, "settings")
    def test_returns_none_when_r2_not_configured(self, mock_settings):
        mock_settings.R2_ENDPOINT_URL = None

        client = storage._get_s3_client()

        assert client is None

    @patch.object(storage, "settings")
    def test_returns_none_when_endpoint_empty_string(self, mock_settings):
        mock_settings.R2_ENDPOINT_URL = ""

        client = storage._get_s3_client()

        assert client is None


# ---------------------------------------------------------------------------
# upload_file
# ---------------------------------------------------------------------------


class TestUploadFile:
    """Tests for upload_file."""

    @patch.object(storage, "_get_s3_client")
    @patch.object(storage, "settings")
    def test_upload_success(self, mock_settings, mock_get_client):
        mock_settings.R2_BUCKET_NAME = "test-bucket"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = storage.upload_file("docs/file.pdf", b"content", "application/pdf")

        assert result is True
        mock_client.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="docs/file.pdf",
            Body=b"content",
            ContentType="application/pdf",
        )

    @patch.object(storage, "_get_s3_client")
    @patch.object(storage, "settings")
    def test_upload_default_content_type(self, mock_settings, mock_get_client):
        mock_settings.R2_BUCKET_NAME = "test-bucket"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        storage.upload_file("key", b"data")

        mock_client.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="key",
            Body=b"data",
            ContentType="application/octet-stream",
        )

    @patch.object(storage, "_get_s3_client")
    def test_upload_returns_false_when_client_not_configured(self, mock_get_client):
        mock_get_client.return_value = None

        result = storage.upload_file("key", b"data")

        assert result is False

    @patch.object(storage, "_get_s3_client")
    @patch.object(storage, "settings")
    def test_upload_returns_false_on_client_error(self, mock_settings, mock_get_client):
        mock_settings.R2_BUCKET_NAME = "test-bucket"
        mock_client = MagicMock()
        mock_client.put_object.side_effect = _make_client_error("InternalError", "Boom")
        mock_get_client.return_value = mock_client

        result = storage.upload_file("key", b"data")

        assert result is False

    @patch.object(storage, "_get_s3_client")
    @patch.object(storage, "settings")
    def test_upload_logs_error_on_client_error(self, mock_settings, mock_get_client, caplog):
        mock_settings.R2_BUCKET_NAME = "test-bucket"
        mock_client = MagicMock()
        mock_client.put_object.side_effect = _make_client_error()
        mock_get_client.return_value = mock_client

        import logging

        with caplog.at_level(logging.ERROR, logger="app.services.storage"):
            storage.upload_file("uploads/fail.txt", b"data")

        assert "R2 upload failed for uploads/fail.txt" in caplog.text


# ---------------------------------------------------------------------------
# download_file
# ---------------------------------------------------------------------------


class TestDownloadFile:
    """Tests for download_file."""

    @patch.object(storage, "_get_s3_client")
    @patch.object(storage, "settings")
    def test_download_success(self, mock_settings, mock_get_client):
        mock_settings.R2_BUCKET_NAME = "test-bucket"
        mock_body = MagicMock()
        mock_body.read.return_value = b"file-content"
        mock_client = MagicMock()
        mock_client.get_object.return_value = {"Body": mock_body}
        mock_get_client.return_value = mock_client

        result = storage.download_file("docs/file.pdf")

        assert result == b"file-content"
        mock_client.get_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="docs/file.pdf",
        )

    @patch.object(storage, "_get_s3_client")
    def test_download_returns_none_when_client_not_configured(self, mock_get_client):
        mock_get_client.return_value = None

        result = storage.download_file("key")

        assert result is None

    @patch.object(storage, "_get_s3_client")
    @patch.object(storage, "settings")
    def test_download_returns_none_on_client_error(self, mock_settings, mock_get_client):
        mock_settings.R2_BUCKET_NAME = "test-bucket"
        mock_client = MagicMock()
        mock_client.get_object.side_effect = _make_client_error("NoSuchKey", "Not found")
        mock_get_client.return_value = mock_client

        result = storage.download_file("missing/key.txt")

        assert result is None

    @patch.object(storage, "_get_s3_client")
    @patch.object(storage, "settings")
    def test_download_logs_error_on_client_error(self, mock_settings, mock_get_client, caplog):
        mock_settings.R2_BUCKET_NAME = "test-bucket"
        mock_client = MagicMock()
        mock_client.get_object.side_effect = _make_client_error()
        mock_get_client.return_value = mock_client

        import logging

        with caplog.at_level(logging.ERROR, logger="app.services.storage"):
            storage.download_file("downloads/missing.bin")

        assert "R2 download failed for downloads/missing.bin" in caplog.text


# ---------------------------------------------------------------------------
# delete_file
# ---------------------------------------------------------------------------


class TestDeleteFile:
    """Tests for delete_file."""

    @patch.object(storage, "_get_s3_client")
    @patch.object(storage, "settings")
    def test_delete_success(self, mock_settings, mock_get_client):
        mock_settings.R2_BUCKET_NAME = "test-bucket"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = storage.delete_file("old/file.pdf")

        assert result is True
        mock_client.delete_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="old/file.pdf",
        )

    @patch.object(storage, "_get_s3_client")
    def test_delete_returns_false_when_client_not_configured(self, mock_get_client):
        mock_get_client.return_value = None

        result = storage.delete_file("key")

        assert result is False

    @patch.object(storage, "_get_s3_client")
    @patch.object(storage, "settings")
    def test_delete_returns_false_on_client_error(self, mock_settings, mock_get_client):
        mock_settings.R2_BUCKET_NAME = "test-bucket"
        mock_client = MagicMock()
        mock_client.delete_object.side_effect = _make_client_error("AccessDenied", "Forbidden")
        mock_get_client.return_value = mock_client

        result = storage.delete_file("key")

        assert result is False

    @patch.object(storage, "_get_s3_client")
    @patch.object(storage, "settings")
    def test_delete_logs_error_on_client_error(self, mock_settings, mock_get_client, caplog):
        mock_settings.R2_BUCKET_NAME = "test-bucket"
        mock_client = MagicMock()
        mock_client.delete_object.side_effect = _make_client_error()
        mock_get_client.return_value = mock_client

        import logging

        with caplog.at_level(logging.ERROR, logger="app.services.storage"):
            storage.delete_file("delete/fail.txt")

        assert "R2 delete failed for delete/fail.txt" in caplog.text


# ---------------------------------------------------------------------------
# generate_presigned_url
# ---------------------------------------------------------------------------


class TestGeneratePresignedUrl:
    """Tests for generate_presigned_url."""

    @patch.object(storage, "_get_s3_client")
    @patch.object(storage, "settings")
    def test_presigned_url_success(self, mock_settings, mock_get_client):
        mock_settings.R2_BUCKET_NAME = "test-bucket"
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "https://r2.example.com/signed"
        mock_get_client.return_value = mock_client

        result = storage.generate_presigned_url("docs/file.pdf")

        assert result == "https://r2.example.com/signed"
        mock_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "test-bucket", "Key": "docs/file.pdf"},
            ExpiresIn=3600,
        )

    @patch.object(storage, "_get_s3_client")
    @patch.object(storage, "settings")
    def test_presigned_url_custom_expiry(self, mock_settings, mock_get_client):
        mock_settings.R2_BUCKET_NAME = "test-bucket"
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "https://signed"
        mock_get_client.return_value = mock_client

        storage.generate_presigned_url("key", expires_in=600)

        mock_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "test-bucket", "Key": "key"},
            ExpiresIn=600,
        )

    @patch.object(storage, "_get_s3_client")
    def test_presigned_url_returns_none_when_client_not_configured(self, mock_get_client):
        mock_get_client.return_value = None

        result = storage.generate_presigned_url("key")

        assert result is None

    @patch.object(storage, "_get_s3_client")
    @patch.object(storage, "settings")
    def test_presigned_url_returns_none_on_client_error(self, mock_settings, mock_get_client):
        mock_settings.R2_BUCKET_NAME = "test-bucket"
        mock_client = MagicMock()
        mock_client.generate_presigned_url.side_effect = _make_client_error()
        mock_get_client.return_value = mock_client

        result = storage.generate_presigned_url("key")

        assert result is None

    @patch.object(storage, "_get_s3_client")
    @patch.object(storage, "settings")
    def test_presigned_url_logs_error_on_client_error(self, mock_settings, mock_get_client, caplog):
        mock_settings.R2_BUCKET_NAME = "test-bucket"
        mock_client = MagicMock()
        mock_client.generate_presigned_url.side_effect = _make_client_error()
        mock_get_client.return_value = mock_client

        import logging

        with caplog.at_level(logging.ERROR, logger="app.services.storage"):
            storage.generate_presigned_url("presign/fail.txt")

        assert "R2 presigned URL failed for presign/fail.txt" in caplog.text
