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
     MAX(recommendation."dateCreated") AS last_recommendation_date, 
     "userId"
    FROM recommendation 
    GROUP BY "userId"
    '''

    text_query_bookings_grouped_by_user = '''
    SELECT 
     MIN(booking."dateCreated") AS date, 
     SUM(booking.quantity) AS number_of_bookings,
     "userId"
    FROM booking 
    JOIN stock ON stock.id = booking."stockId"
    JOIN offer ON offer.id = stock."offerId"
    WHERE offer.type != 'ThingType.ACTIVATION'
    GROUP BY "userId"
    '''

    text_query_non_cancelled_bookings_grouped_by_user = '''
    SELECT 
     SUM(booking.quantity) AS number_of_bookings,
     "userId"
    FROM booking 
    JOIN stock ON stock.id = booking."stockId"
    JOIN offer ON offer.id = stock."offerId"
    WHERE offer.type != 'ThingType.ACTIVATION'
     AND booking."isCancelled" IS FALSE
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

    text_query_first_booking_on_third_category = '''
    WITH bookings_on_distinct_types AS (SELECT DISTINCT ON (offer.type, booking."userId") offer.type, booking."userId", booking."dateCreated" 
    FROM booking 
    JOIN stock ON stock.id = booking."stockId" 
    JOIN offer ON offer.id = stock."offerId" 
   WHERE offer.type != 'ThingType.ACTIVATION'
   ORDER BY offer.type, booking."userId", booking."dateCreated" ASC
  )  
      
  SELECT  
   ordered_dates."dateCreated" AS date,  
   ordered_dates."userId"  
  FROM (  
   SELECT   
    ROW_NUMBER()  
     OVER(  
      PARTITION BY "userId"   
      ORDER BY bookings_on_distinct_types."dateCreated" ASC  
     ) AS rank, bookings_on_distinct_types."dateCreated",   
    bookings_on_distinct_types."userId"   
   FROM bookings_on_distinct_types   
      ) AS ordered_dates  
  WHERE ordered_dates.rank = 3  
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
        bookings_grouped_by_user.date AS "Date de première réservation",
        second_booking_dates.date AS "Date de deuxième réservation",
        first_booking_on_third_category.date as "Date de première réservation dans 3 catégories différentes",
        recommendation_dates.last_recommendation_date AS "Date de dernière recommandation",
        bookings_grouped_by_user.number_of_bookings AS "Nombre de réservations totales",
        non_cancelled_bookings_grouped_by_user.number_of_bookings AS "Nombre de réservations non annulées" 
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
        LEFT JOIN ({text_query_bookings_grouped_by_user})
         AS bookings_grouped_by_user
         ON bookings_grouped_by_user."userId" = "user".id 
        LEFT JOIN ({text_query_second_booking_date})
         AS second_booking_dates
         ON second_booking_dates."userId" = "user".id 
        LEFT JOIN ({text_query_first_booking_on_third_category})
         AS first_booking_on_third_category
         ON first_booking_on_third_category."userId" = "user".id 
        LEFT JOIN ({text_query_non_cancelled_bookings_grouped_by_user})
         AS non_cancelled_bookings_grouped_by_user
         ON non_cancelled_bookings_grouped_by_user."userId" = "user".id 
        WHERE "user"."canBookFreeOffers";
        ''',
        connection
    )
