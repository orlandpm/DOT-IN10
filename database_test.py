from werkzeug.security import generate_password_hash, check_password_hash
import database

db = database.SqliteDBnexDatabase()
# db.create_user("KAIROL", "KAIROL", "KAIROL", 5, generate_password_hash("KAIROL"))
# db.create_user("Friday", "Friday", "Friday", 3, generate_password_hash("Friday"))
kairol_id = db.get_id_by_user("KAIROL")[0]['BirdId']
Friday_id = db.get_id_by_user("Friday")[0]['BirdId']

db.add_friend_request(kairol_id, Friday_id)
 
  