import pytest

from product_twin.supabase_gateway import SupabaseGateway


def test_owned_storage_path_is_accepted() -> None:
    SupabaseGateway.validate_owned_path("user-a", "user-a/project/output.png")


@pytest.mark.parametrize(
    "path",
    ["user-b/project/output.png", "../secret", "/user-a/absolute.png", "user-a/../secret"],
)
def test_unowned_or_traversal_storage_path_is_rejected(path: str) -> None:
    with pytest.raises((ValueError, PermissionError)):
        SupabaseGateway.validate_owned_path("user-a", path)
