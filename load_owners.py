import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.environ["SUPABASE_DB_URL"])
cursor = conn.cursor()

# Each entry: display_name, [(platform, external_id), ...]
owners_data = [
    ("Patrick Lacey", [
        ("espn", "034D3560-DBF6-4DFB-8D35-60DBF64DFB7F"),
    ]),
    ("Sean Southwell", [
        ("espn", "84117BAC-A9A0-4359-9727-70A923507F68"),
    ]),
    ("Kyle Pettit", [
        ("espn", "89983C69-528E-4AEA-983C-69528E7AEABC"),
    ]),
    ("Gordon Hobbis", [
        ("espn", "94679DD6-39F4-40B2-9D53-456B9AF4F1F9"),
    ]),
    ("Brian Fell", [
        ("espn", "CE4217E5-7F09-424F-8217-E57F09E24F59"),
        ("sleeper", "994108712421806080"),
    ]),
    ("Brian Fell (BigBrianF)", [
        ("espn", "D69DBA47-7CAC-4DFB-A7DE-9075120A084D"),
        ("espn", "335C0F9E-9E39-4CD3-B792-BB9BCC05C2FC"),
        ("sleeper", "994757347165810688"),
    ]),
    ("Patrick Larrison", [
        ("espn", "CE6F258D-D98C-455C-AF25-8DD98CE55C78"),
    ]),
    ("Sal Gargiulo", [
        ("espn", "E7C2E268-11BC-4742-9CBB-E44F80CB9E0D"),
        ("sleeper", "862532554870337536"),
    ]),
    ("Ed Dollive", [
        ("espn", "F0A0DF03-0D0D-4CEC-9F6D-9FF77A7EB297"),
    ]),
    ("Kevin Caswell", [
        ("espn", "FDCFEB04-D94D-4110-8FEB-04D94D31109E"),
        ("sleeper", "994727767172243456"),
    ]),
    ("Matt Dollive", [
        ("espn", "132FEC9D-7EF2-4113-BC29-90529F4A5369"),
        ("espn", "3B9B59D9-D541-42C5-A369-67F2F06E55DB"),
    ]),
    ("James Petrides", [
        ("espn", "61F3C8BB-C8EE-4F87-AD92-4E50F0813631"),
        ("sleeper", "994276076346023936"),
    ]),
    ("Chris Sonde", [
        ("espn", "65DEB4CB-C63B-484A-9EB4-CBC63B084AB6"),
        ("espn", "77B4ACD1-2318-4E0C-8951-00CEAB94F71F"),
        ("sleeper", "994727996458156032"),
    ]),
    ("Trent Carr", [
        ("espn", "9C48BB9B-DD18-47EE-BC74-EA4A134D8223"),
    ]),
    ("Ben Tigar", [
        ("espn", "D3AEA312-FE87-40BA-8712-C27693D95400"),
        ("sleeper", "995002066449862656"),
    ]),
    ("Mike Matthews", [
        ("espn", "18596B26-6159-4A6A-8465-8DF0184B2737"),
        ("sleeper", "994112915890348032"),
    ]),
    ("Domenico Gargiulo", [
        ("espn", "DFEBFE2E-D158-4EF2-BAD7-47AF9C6B223E"),
        ("sleeper", "1126325422121181184"),
    ]),
    ("Corey Holcomb", [
        ("espn", "3B7B2AB2-4D8A-473C-9DFE-727F8BDE2BC2"),
        ("sleeper", "994727287503278080"),
    ]),
    ("Xavier", [
        ("sleeper", "1263375916910788608"),
    ]),
    ("Ryan Jaspan", [
        ("espn", "8041A71B-A2DA-4961-AD2D-F7D65DF3CC67"),
        ("sleeper", "991788583503609856"),
    ]),
    ("Jon Shan", [
        ("sleeper", "994676336096595968"),
    ]),
    ("D3Vries", [
        ("sleeper", "994729517677600768"),
    ]),
    ("Will Mruz", [
        ("sleeper", "994768218264842240"),
    ]),
    ("acaswell04", [
        ("sleeper", "995148550860222464"),
    ]),
    ("mcaswell154 (co-owner with acaswell04, 2023)", [
        ("sleeper", "995149491927830528"),
    ]),
    ("Metsrule1997", [
        ("sleeper", "694719465350320128"),
    ]),
    ("Kyle Sottosanti", [
        ("sleeper", "871295341524373504"),
    ]),
]

for display_name, ids in owners_data:
    cursor.execute(
        "INSERT INTO owners (display_name) VALUES (%s) RETURNING owner_id;",
        (display_name,)
    )
    owner_id = cursor.fetchone()[0]

    for platform, external_id in ids:
        cursor.execute(
            "INSERT INTO owner_external_ids (owner_id, platform, external_id) VALUES (%s, %s, %s);",
            (owner_id, platform, external_id)
        )

    print(f"Inserted {display_name} with {len(ids)} external ID(s)")

conn.commit()
print(f"All {len(owners_data)} owners loaded.")

cursor.close()
conn.close()