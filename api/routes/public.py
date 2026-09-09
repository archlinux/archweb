from datetime import datetime, timezone

from django.contrib.auth.models import User
from django.db.models import Q
from ninja import Router

from api.schemas.public import PGPEdgeSchema, PGPKeysSchema, PGPNodeSchema
from devel.models import MasterKey, PGPSignature, UserProfile

router = Router(tags=["public"])


@router.get("/", response=PGPKeysSchema, url_name="pgp-keys")
def master_keys(request):
    profile_ids = UserProfile.allowed_repos.through.objects.values('userprofile_id')
    users = User.objects.filter(
        is_active=True, userprofile__id__in=profile_ids
    ).order_by('first_name', 'last_name')
    nodes = [
        PGPNodeSchema(
            name=user.get_full_name(),
            key=user.userprofile.pgp_key or None,
            group='packager',
        )
        for user in users
    ]

    master = MasterKey.objects.select_related('owner').filter(revoked__isnull=True)
    nodes.extend(
        PGPNodeSchema(
            name='Master Key (%s)' % key.owner.get_full_name(),
            key=key.pgp_key or None,
            group='master',
        )
        for key in master
    )

    not_expired = Q(expires__gt=datetime.now(timezone.utc)) | Q(expires__isnull=True)
    signatures = PGPSignature.objects.filter(not_expired, revoked__isnull=True)
    edges = [
        PGPEdgeSchema(signee=sig.signee, signer=sig.signer)
        for sig in signatures
    ]

    return PGPKeysSchema(nodes=nodes, edges=edges)
