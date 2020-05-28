"""renamme_order_function_in_discovery_view

Revision ID: a15ec00563d4
Revises: 3a5629a53c17
Create Date: 2020-05-28 09:00:59.777246

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a15ec00563d4'
down_revision = '3a5629a53c17'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DROP MATERIALIZED VIEW IF EXISTS discovery_view;")

    op.execute("ALTER FUNCTION get_recommendable_offers_ordered_by_digital_offers "
               "RENAME TO get_ordered_recommendable_offers;")

    op.execute(f"""
        CREATE OR REPLACE FUNCTION get_ordered_recommendable_offers()
        RETURNS TABLE (
            criterion_score BIGINT,
            id BIGINT,
            "venueId" BIGINT,
            type VARCHAR,
            name VARCHAR,
            url VARCHAR,
            "isNational" BOOLEAN,
            partitioned_offers BIGINT
        ) AS $body$
        BEGIN
            RETURN QUERY
            SELECT
                (SELECT * FROM get_offer_score(offer.id)) AS criterion_score,
                offer.id AS id,
                offer."venueId" AS "venueId",
                offer.type AS type,
                offer.name AS name,
                offer.url AS url,
                offer."isNational" AS "isNational",
                ROW_NUMBER() OVER (
                    ORDER BY
                    (
                        SELECT COALESCE(SUM(criterion."scoreDelta"), 0) AS coalesce_1
                        FROM criterion, offer_criterion
                        WHERE criterion.id = offer_criterion."criterionId"
                        AND offer_criterion."offerId" = offer.id
                    ) DESC,
                    offer.url IS NOT NULL DESC,
                    RANDOM()
                ) AS partitioned_offers
            FROM offer
            WHERE offer.id IN (SELECT * FROM get_active_offers_ids(TRUE))
            ORDER BY ROW_NUMBER() OVER (
                ORDER BY
                (
                    SELECT COALESCE(SUM(criterion."scoreDelta"), 0) AS coalesce_1
                    FROM criterion, offer_criterion
                    WHERE criterion.id = offer_criterion."criterionId"
                    AND offer_criterion."offerId" = offer.id
                ) DESC,
                offer.url IS NOT NULL DESC,
                RANDOM()
            );
        END
        $body$
        LANGUAGE plpgsql;
    """)

    op.execute(f"""
        CREATE MATERIALIZED VIEW IF NOT EXISTS discovery_view AS
            SELECT
                ROW_NUMBER() OVER ()                AS "offerDiscoveryOrder",
                recommendable_offers.id             AS id,
                recommendable_offers."venueId"      AS "venueId",
                recommendable_offers.type           AS type,
                recommendable_offers.name           AS name,
                recommendable_offers.url            AS url,
                recommendable_offers."isNational"   AS "isNational",
                offer_mediation.id                  AS "mediationId"
            FROM (SELECT * FROM get_ordered_recommendable_offers()) AS recommendable_offers
            LEFT OUTER JOIN mediation AS offer_mediation ON recommendable_offers.id = offer_mediation."offerId"
                AND offer_mediation."isActive"
            ORDER BY recommendable_offers.partitioned_offers;
    """)


def downgrade():
    op.execute("DROP MATERIALIZED VIEW IF EXISTS discovery_view;")

    op.execute("ALTER FUNCTION get_ordered_recommendable_offers "
               "RENAME TO get_recommendable_offers_ordered_by_digital_offers;")

    op.execute("""
        CREATE OR REPLACE FUNCTION get_recommendable_offers_ordered_by_digital_offers()
        RETURNS TABLE (
            criterion_score BIGINT,
            id BIGINT,
            "venueId" BIGINT,
            type VARCHAR,
            name VARCHAR,
            url VARCHAR,
            "isNational" BOOLEAN,
            partitioned_offers BIGINT
        ) AS $body$
        BEGIN
            RETURN QUERY
            SELECT
                (SELECT * FROM get_offer_score(offer.id)) AS criterion_score,
                offer.id AS id,
                offer."venueId" AS "venueId",
                offer.type AS type,
                offer.name AS name,
                offer.url AS url,
                offer."isNational" AS "isNational",
                ROW_NUMBER() OVER (
                    ORDER BY
                    (
                        SELECT COALESCE(SUM(criterion."scoreDelta"), 0) AS coalesce_1
                        FROM criterion, offer_criterion
                        WHERE criterion.id = offer_criterion."criterionId"
                        AND offer_criterion."offerId" = offer.id
                    ) DESC,
                    offer.url IS NOT NULL DESC,
                    RANDOM()
                ) AS partitioned_offers
            FROM offer
            WHERE offer.id IN (SELECT * FROM get_active_offers_ids(TRUE))
            ORDER BY ROW_NUMBER() OVER (
                ORDER BY
                (
                    SELECT COALESCE(SUM(criterion."scoreDelta"), 0) AS coalesce_1
                    FROM criterion, offer_criterion
                    WHERE criterion.id = offer_criterion."criterionId"
                    AND offer_criterion."offerId" = offer.id
                ) DESC,
                offer.url IS NOT NULL DESC,
                RANDOM()
            );
        END
        $body$
        LANGUAGE plpgsql;
    """)

    op.execute(f"""
            CREATE MATERIALIZED VIEW IF NOT EXISTS discovery_view AS
                SELECT
                    ROW_NUMBER() OVER ()                AS "offerDiscoveryOrder",
                    recommendable_offers.id             AS id,
                    recommendable_offers."venueId"      AS "venueId",
                    recommendable_offers.type           AS type,
                    recommendable_offers.name           AS name,
                    recommendable_offers.url            AS url,
                    recommendable_offers."isNational"   AS "isNational",
                    offer_mediation.id                  AS "mediationId"
                FROM (SELECT * FROM get_recommendable_offers_ordered_by_digital_offers()) AS recommendable_offers
                LEFT OUTER JOIN mediation AS offer_mediation ON recommendable_offers.id = offer_mediation."offerId"
                    AND offer_mediation."isActive"
                ORDER BY recommendable_offers.partitioned_offers;
        """)
