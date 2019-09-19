import pandas

from models.db import db


def get_all_experimentation_users_details() -> pandas.DataFrame:
    connection = db.engine.connect()
    text_query_validated_activation_booking = '''
    (
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
     ) AS validated_activation_booking
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
        END AS "Date d'activation"
        FROM "user"
        LEFT JOIN booking ON booking."userId" = "user".id
        LEFT JOIN stock ON stock.id = booking."stockId"
        LEFT JOIN offer ON offer.id = stock."offerId" 
         AND offer.type = 'ThingType.ACTIVATION'
        LEFT JOIN {text_query_validated_activation_booking} ON validated_activation_booking."userId" = "user".id
        WHERE "user"."canBookFreeOffers";
        ''',
        connection
    )

'''
 SELECT  
  COALESCE(validated_activation_booking.issued_at, "user"."dateCreated") 
 FROM "user" 
 LEFT JOIN  
  ON validated_activation_booking."userId" = "user".id 
 WHERE "user"."canBookFreeOffers";
'''