"""Create a fake user who has already liked you, so you can test match + chat.

Usage: uv run python scripts/seed_match_partner.py [your-email]
Without an email, it picks the most recent real Spotify user.
"""

import sys

from api.config import settings
from matching.state_machine import record_interaction
from shared.db import get_engine
from shared.models import User, UserMusicProfile
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

PARTNER_EMAIL = "match-partner@example.com"


def main() -> None:
    engine = get_engine(settings.database_url)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with Session() as db:
        if len(sys.argv) > 1:
            me = db.scalar(select(User).where(User.email == sys.argv[1]))
        else:
            me = db.scalar(
                select(User)
                .where(User.spotify_id.is_not(None))
                .order_by(User.created_at.desc())
            )
        if me is None:
            raise SystemExit("Could not find your user. Log in first, or pass your email.")

        if me.latitude is None or me.longitude is None:
            me.latitude, me.longitude = 31.10, 77.17  # Shimla
            me.max_distance_km = 100.0
            print("Your location was empty; set it to Shimla, 100 km.")

        my_profile = db.scalar(
            select(UserMusicProfile).where(UserMusicProfile.user_id == me.id)
        )
        if my_profile is None:
            raise SystemExit("You have no music profile yet. Finish onboarding first.")

        partner = db.scalar(select(User).where(User.email == PARTNER_EMAIL))
        if partner is None:
            partner = User(
                email=PARTNER_EMAIL,
                display_name="Match Partner",
                latitude=me.latitude + 0.01,
                longitude=me.longitude + 0.01,
                max_distance_km=100.0,
            )
            db.add(partner)
            db.commit()

            # Copy your artists so the compatibility score is high.
            db.add(
                UserMusicProfile(
                    user_id=partner.id,
                    top_artists=my_profile.top_artists,
                    top_tracks={"items": []},
                    recently_played={"items": []},
                    top_genres=my_profile.top_genres or {},
                    time_window=my_profile.time_window,
                    is_stale=False,
                )
            )
            db.commit()

        record_interaction(db, partner.id, me.id, "like")
        db.commit()
        print(f"Done. 'Match Partner' has liked {me.display_name}. Open /feed and like them back.")


if __name__ == "__main__":
    main()