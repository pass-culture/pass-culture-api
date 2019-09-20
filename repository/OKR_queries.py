import pandas

from models.db import db


def get_all_experimentation_users_details() -> pandas.DataFrame:
    connection = db.engine.connect()
    text_query_validated_activation_booking = '''
    SELECT activity.issued_at, booking."userId" 
    FROM activity 
    JOIN booking   
     ON (activity.old_data ->> 'id')::int = booking.id 
     AND booking."isUsed" 
    JOIN stock 
     ON stock.id = booking."stockId" 
    JOIN offer 
     ON stock."offerId" = offer.id 
     AND offer.type = 'ThingType.ACTIVATION' 
    WHERE  
     activity.table_name='booking'   
     AND activity.verb='update'   
     AND activity.changed_data ->> 'isUsed'='true'  
    '''

    text_query_typeform_filled = '''
    SELECT activity.issued_at, "user".id AS "userId"
     FROM activity  
     JOIN "user"    
      ON (activity.old_data ->> 'id')::int = "user".id  
      AND activity.table_name='user'    
      AND activity.verb='update'    
      AND activity.changed_data ->> 'needsToFillCulturalSurvey'='false'
    '''

    text_query_recommendation_dates = '''
    SELECT 
     MIN(recommendation."dateCreated") AS first_recommendation_date, 
     "userId"
    FROM recommendation 
    GROUP BY "userId"
    '''

    text_query_first_booking_date = '''
    SELECT 
     MIN(booking."dateCreated") AS date, 
     "userId"
    FROM booking 
    JOIN stock ON stock.id = booking."stockId"
    JOIN offer ON offer.id = stock."offerId"
    WHERE offer.type != 'ThingType.ACTIVATION'
    GROUP BY "userId"
    '''

    text_query_second_booking_date = '''
    SELECT 
     ordered_dates."dateCreated" AS date, 
     ordered_dates."userId"  
     FROM ( 
      SELECT ROW_NUMBER()  
      OVER(PARTITION BY "userId" ORDER BY booking."dateCreated" ASC) AS rank, booking."dateCreated", booking."userId"  
      FROM booking 
      JOIN stock ON stock.id = booking."stockId"
      JOIN offer ON offer.id = stock."offerId"
      WHERE offer.type != 'ThingType.ACTIVATION'
     ) AS ordered_dates  
     WHERE ordered_dates.rank = 2
    '''

    return pandas.read_sql_query(
        f'''
        SELECT 
         CASE WHEN booking."isUsed" THEN 1
              ELSE 2 
         END AS "Vague d'expérimentation",
         "user"."departementCode" AS "Département",
         CASE WHEN booking."isUsed" THEN validated_activation_booking.issued_at
              ELSE "user"."dateCreated"
        END AS "Date d'activation",
        typeform_filled.issued_at AS "Date de remplissage du typeform",
        recommendation_dates.first_recommendation_date AS "Date de première connection",
        first_booking_dates.date AS "Date de première réservation",
        second_booking_dates.date AS "Date de deuxième réservation"
        FROM "user"
        LEFT JOIN booking ON booking."userId" = "user".id
        LEFT JOIN stock ON stock.id = booking."stockId"
        LEFT JOIN offer ON offer.id = stock."offerId" 
         AND offer.type = 'ThingType.ACTIVATION'
        LEFT JOIN ({text_query_validated_activation_booking}) 
         AS validated_activation_booking 
         ON validated_activation_booking."userId" = "user".id
        LEFT JOIN ({text_query_typeform_filled}) 
         AS typeform_filled
         ON typeform_filled."userId" = "user".id
        LEFT JOIN ({text_query_recommendation_dates}) 
         AS recommendation_dates
         ON recommendation_dates."userId" = "user".id
        LEFT JOIN ({text_query_first_booking_date})
         AS first_booking_dates
         ON first_booking_dates."userId" = "user".id 
        LEFT JOIN ({text_query_second_booking_date})
         AS second_booking_dates
         ON second_booking_dates."userId" = "user".id 
        WHERE "user"."canBookFreeOffers";
        ''',
        connection
    )
