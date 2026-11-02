"""Builds the synthetic review dataset for the AI Review Analyzer demo.

Every review is hand-written. Six problems are planted on purpose (ground truth),
plus a few "traps": real complaints that appear only 1-2 times and should NOT
become action items. The workflow never sees the labels in this file.

Usage: python build_dataset.py <output data folder>
"""
import csv
import random
import sys
from datetime import date, timedelta
from pathlib import Path

PRODUCTS = [
    ("PS-HAR-001", "No-Pull Dog Harness", "Sizes S/M/L/XL by chest girth: S 40-55 cm, M 55-70 cm, L 70-85 cm, XL 85-100 cm. Front and back clips, reflective strips, padded chest plate, back handle."),
    ("PS-BED-002", "Orthopedic Memory Foam Dog Bed", "10 cm memory foam, removable cover, machine washable at 30 °C, non-slip base, sizes M/L/XL."),
    ("PS-LIT-003", "Clumping Cat Litter 10 L", "Clumping clay litter, 10 L bag, 99% dust-free, fresh scent, low tracking."),
    ("PS-FED-004", "Automatic Pet Feeder with App", "4 L hopper, Wi-Fi app scheduling (2.4 GHz), up to 10 meals a day, battery backup, voice recording."),
    ("PS-CAR-005", "Cat Carrier Backpack", "Ventilated backpack with bubble window, for cats up to 6 kg, padded shoulder straps, chest strap, airline-friendly size."),
    ("PS-TOY-006", "Rubber Chew Toy with Treat Slot", "Natural rubber chew toy with a treat slot, size M, for medium dogs."),
    ("PS-FOD-007", "Grain-Free Adult Dog Food 12 kg", "Grain-free adult dog food, chicken and sweet potato, 12 kg bag."),
    ("PS-SCR-008", "Sisal Scratching Post 80 cm", "Sisal scratching post, 80 cm tall, weighted base, easy assembly."),
]

# Planted problems: (issue_id, sku, accepted themes, description)
ISSUES = {
    "I1": ("PS-HAR-001", "sizing_fit", "Harness runs small: the size chart is off by about one size"),
    "I2": ("PS-BED-002", "cleaning_washing|durability", "Bed cover shrinks after washing at 30 °C as instructed"),
    "I3": ("PS-LIT-003", "dust", "Litter is dusty when pouring, despite the '99% dust-free' claim"),
    "I4": ("PS-FED-004", "app_connectivity", "Feeder loses Wi-Fi / goes offline in the app"),
    "I5": ("PS-CAR-005", "durability|build_quality", "Carrier zipper splits or comes off the track"),
    "I6": ("PS-FOD-007", "packaging", "Food bag arrives torn or punctured"),
}

# Traps: real complaints that appear 1-2 times per product. They should not become actions.
TRAPS = {
    "T1": ("PS-SCR-008", "build_quality", "Scratching post wobbles (2 reviews)"),
    "T2": ("PS-TOY-006", "durability", "Toy destroyed by a strong chewer (2 reviews)"),
    "T3": ("PS-FED-004", "noise", "Feeder motor is loud (2 reviews)"),
    "T4": ("PS-LIT-003", "smell", "Litter scent too strong (2 reviews)"),
    "T5": ("PS-CAR-005", "sizing_fit", "Carrier too small for a big cat (2 reviews)"),
    "T6": ("PS-FED-004", "build_quality|ease_of_use", "Large kibble jams the feeder (2 reviews)"),
    "T7": ("PS-TOY-006", "pet_acceptance", "Dog not interested in the toy (2 reviews)"),
}

# (rating, title, text, label) — label is an ISSUES/TRAPS key or None
R = {
"PS-HAR-001": [
    (2, "Runs at least one size small", "Measured my lab's chest twice, 78 cm, ordered L per the chart. Couldn't close the buckle. Had to send it back for an XL.", "I1"),
    (3, "Good harness, wrong size chart", "Quality is fine and he doesn't pull as much. But the M fits like an S. Size up.", "I1"),
    (4, "Love it, but order a size up", "Super comfy padding and the front clip really works. Only thing: the chart is off, my beagle needed L, not M.", "I1"),
    (1, "Too tight", "Too tight under the legs even on the loosest setting. Left red marks after a walk.", "I1"),
    (2, "chart is wrong", "followed the size chart exactly and it was way too small for my husky. exchange took 2 weeks", "I1"),
    (3, "Tight around the chest", "Her chest is 62 cm, so the chart says M. The M barely closed. Went up to L and it's perfect now.", "I1"),
    (2, "Great, if your dog is smaller than the chart says", "Ordered S for my terrier. Fits our neighbour's chihuahua much better.", "I1"),
    (4, "Second one fits", "First one (M) was too snug, exchanged it for L without problems. The L is great, and the reflective strips are bright at night.", "I1"),
    (2, "Straps max out too early", "The adjusters run out of length long before the girth range on the label. Disappointing for the price.", "I1"),
    (5, "No more pulling", "The front clip changed our walks. She used to drag me to every tree.", None),
    (5, "Easy to put on", "Step in, two buckles, done in 10 seconds. My old dog hates things going over his head, so this is perfect.", None),
    (4, "Solid build", "Stitching looks strong and the buckles feel sturdy.", None),
    (5, "Reflective strips actually work", "We walk late in winter and cars see us now. Very bright in headlights.", None),
    (5, "Comfortable", "No rubbing under the legs, the padding is soft. He doesn't try to take it off.", None),
    (4, "Good value", "Cheaper than the brand at our local pet shop and works just as well.", None),
    (3, "Colour is different", "Ordered forest green, got something closer to grey. Works fine though.", None),
    (2, "Chewed through in a week", "My puppy chewed the side strap in a week. Maybe not for chewers.", None),
    (3, "Slow delivery", "Took 9 days instead of 3. The harness itself is ok.", None),
    (5, "Handle on the back is useful", "The handle helps a lot when I lift him into the car.", None),
    (4, "Does the job", "Simple, works, no complaints so far.", None),
    (5, "Bought a second one", "Got one for each of our dogs. Both are happy.", None),
    (5, "Great for hiking", "Used it on a 15 km hike, no chafing and the handle helped on rocks.", None),
    (4, "Buckles stiff at first", "The buckles were stiff for the first few days, fine now.", None),
    (5, "Vet recommended a harness", "Vet said no more collar for his trachea. This one is great.", None),
    (5, "Light and breathable", "Good for summer, he doesn't overheat in it.", None),
    (4, "Fits my border collie well", "Chest 52 cm, took the M, fits nicely with room to adjust.", None),
    (5, "Easy to clean", "Hand washed it after a muddy walk, dry by the morning.", None),
    (5, "Calmer walks", "Less pulling means less stress for both of us.", None),
    (4, "D-ring could be bigger", "Works well, but the front ring is a bit small for our thick leash clip.", None),
    (5, "Excellent", "Exactly what we needed for our young lab.", None),
    (5, "As described", "Everything as on the page, good quality.", None),
    (4, "Comfy for long walks", "No marks after two hours of walking.", None),
    (5, "Our second harness from this store", "Previous one lasted three years, so we bought this one.", None),
    (5, "Reactive dog is easier to manage", "The back handle gives me control when he lunges.", None),
    (5, "Happy", "Good harness, good price.", None),
],
"PS-BED-002": [
    (2, "Cover shrank after first wash", "Washed it at 30 °C exactly as the label says. Now the zip won't close around the foam.", "I2"),
    (3, "Great bed, terrible cover", "My old lab sleeps so much better on it. But after one wash the cover is too small to get back on.", "I2"),
    (2, "Don't wash the cover", "It shrunk by a few centimetres on a gentle 30 degree cycle. Spent 20 minutes wrestling the foam back in.", "I2"),
    (1, "Machine washable? Not really", "The page says machine washable. It came out smaller and now the foam bunches up at the corners.", "I2"),
    (3, "Cover issue", "foam is fantastic but the cover shrinks. had to buy a second cover from another shop", "I2"),
    (4, "Comfy, wash with care", "Dog loves it. Tip: wash the cover cold and air dry it, mine shrank a bit the first time.", "I2"),
    (5, "Our senior dog loves it", "11 years old with stiff hips, he gets up much easier in the morning.", None),
    (5, "Real memory foam", "Thick foam that doesn't flatten. Worth the money.", None),
    (4, "Good support", "Firm enough for our 35 kg shepherd.", None),
    (3, "Smells of foam at first", "Chemical smell for the first 3 days, gone after airing it out.", None),
    (5, "Fits the crate perfectly", "The L fits our large crate exactly.", None),
    (5, "Non-slip bottom", "Doesn't slide on our wooden floor at all.", None),
    (5, "Best purchase for my arthritic dog", "She limps less in the mornings since we got it.", None),
    (4, "Pricey but good", "Not cheap, but you can feel the quality of the foam.", None),
    (5, "Fast delivery", "Arrived next day, well packed.", None),
    (5, "Dog won't leave it", "He ignores the sofa now.", None),
    (4, "Comfortable, a bit firm", "Took him two nights to get used to it.", None),
    (5, "Quality", "Well made, nice thick fabric.", None),
    (5, "Keeps its shape", "Three months in, no dents.", None),
    (4, "Nice colour", "Grey fits our living room.", None),
    (5, "Helped after surgery", "Perfect for recovery after his knee operation.", None),
    (5, "Two dogs share it", "The XL fits both our beagles.", None),
    (3, "Too firm for my small dog", "My 5 kg dog seems to prefer her old soft bed.", None),
    (5, "Great support for big dogs", "Our Great Dane finally has a bed that doesn't flatten.", None),
    (4, "Good bed", "Comfortable and looks good.", None),
    (5, "Worth it", "Should have bought it years ago.", None),
    (5, "Our greyhound approves", "Bony dogs need this kind of foam.", None),
    (4, "Easy to carry", "Light enough to move between rooms.", None),
    (5, "Sleeps through the night now", "No more pacing at night.", None),
    (5, "Great foam", "Dense and comfortable.", None),
    (4, "Good, delivery a bit slow", "Bed is great, delivery took a week.", None),
],
"PS-LIT-003": [
    (2, "So much dust", "A grey cloud every time I pour it. I have to open the window. So much for 99% dust-free.", "I3"),
    (3, "Clumps well, but dusty", "Clumping and smell control are great. Pouring it is a dust storm though.", "I3"),
    (2, "My cat sneezes", "Since switching to this litter my cat sneezes after using the box. Lots of fine dust.", "I3"),
    (4, "Good value, a bit dusty", "Lasts long and clumps hard. Some dust when I fill the box, so I pour slowly.", "I3"),
    (1, "Dust everywhere", "Fine dust settles on the floor around the box and on the shelf above it. Not dust-free at all.", "I3"),
    (2, "Not for allergies", "My partner has asthma and the dust when scooping makes it worse.", "I3"),
    (3, "Pour carefully", "Works fine, but there's a film of white dust on everything near the box after a week.", "I3"),
    (5, "Best clumping I've used", "Rock-hard clumps, no smell. Yes, it's a bit dusty when pouring, but I don't mind.", "I3"),
    (5, "Clumps instantly", "Scooping takes a minute a day now.", None),
    (5, "No smell even with two cats", "Flat is small and you can't smell the box at all.", None),
    (4, "Low tracking", "Much less litter on the floor than our old one.", None),
    (5, "Lasts long", "A 10 L bag lasts us almost a month with one cat.", None),
    (3, "Scent too strong", "The perfume is very strong, I'd prefer an unscented version.", "T4"),
    (3, "Strong perfume", "my cat hesitated to use the box the first day because of the scent", "T4"),
    (5, "Easy to scoop", "Clumps don't break apart.", None),
    (4, "Bag is heavy", "Heavy to carry up the stairs, but that's expected for 10 L.", None),
    (5, "Cat took to it right away", "No transition needed.", None),
    (5, "Great odour control", "Even on day 3 no smell.", None),
    (4, "Good price", "Cheaper than the supermarket brand.", None),
    (5, "Hard clumps, easy cleaning", "The box stays clean.", None),
    (5, "Switched from silica", "Never going back.", None),
    (4, "Works well", "Does what it should.", None),
    (5, "Box stays fresh", "Love it.", None),
    (5, "On subscription", "Ordering every month now.", None),
    (4, "Decent", "Good litter for the price.", None),
    (5, "Best litter", "Tried five brands, this one wins.", None),
    (5, "Good for a multi-cat home", "Three cats, one box, no smell.", None),
    (4, "Nice texture", "Fine grains, soft on paws.", None),
    (5, "Delivered fast", "Two days.", None),
    (2, "Bag arrived split", "The bag was torn and litter spilled in the box.", None),
    (5, "Clumps and no odour", "Exactly as described.", None),
    (4, "Good", "No complaints.", None),
    (5, "Cat approved", "She uses it without any fuss.", None),
    (5, "Great value for money", "Lasts longer than cheaper ones.", None),
],
"PS-FED-004": [
    (2, "Keeps dropping Wi-Fi", "The feeder disconnects from Wi-Fi every couple of days and the app shows it offline.", "I4"),
    (1, "Missed a feeding", "The app lost connection while we were away and the evening meal didn't come out. Not ok for a feeder.", "I4"),
    (3, "Works, app doesn't", "Mechanics are great and portions are accurate. The app keeps saying 'device offline' though.", "I4"),
    (2, "Reconnect every week", "I have to reset it and pair it again every week. Our router is right next to it.", "I4"),
    (3, "Schedule ok, connection bad", "The schedule still runs, but I can't check from work if the cat ate because it shows offline.", "I4"),
    (2, "App is unreliable", "Notifications stopped, then the feeder vanished from the app. Third time this month.", "I4"),
    (4, "Good feeder, flaky app", "Cat is happy and gets fed on time. Only the app connection is flaky, reconnecting helps.", "I4"),
    (2, "2.4 GHz and still drops", "Set it up on 2.4 GHz like the manual says. Still loses connection overnight.", "I4"),
    (5, "No more 5 am wake-ups", "The cat waits for the feeder now, not for me.", None),
    (5, "Accurate portions", "Weighed the portions, very consistent.", None),
    (5, "Easy setup", "Up and running in 10 minutes.", None),
    (4, "Battery backup saved us", "Power cut for 3 hours and it still fed the cat on time.", None),
    (3, "Motor is loud at night", "The motor noise at 3 am wakes us up.", "T3"),
    (3, "Noisy", "The dispensing sound wakes me up at 6.", "T3"),
    (2, "Kibble jammed", "Large kibble jammed twice in the first week.", "T6"),
    (5, "Great for my diabetic cat", "Small meals on a schedule, the vet is happy.", None),
    (5, "Holds a lot", "Fill it once a week.", None),
    (4, "Easy to clean bowl", "The bowl and hopper come apart easily.", None),
    (5, "Cat adapted quickly", "Took her one day.", None),
    (5, "Great when we travel", "Weekend trips are no problem now.", None),
    (4, "Good feeder", "Solid and simple.", None),
    (5, "Love the voice recording", "She runs when she hears my voice.", None),
    (5, "Sturdy", "Our cat tried to knock it over and failed.", None),
    (4, "Lid lock works", "The cat can't get into the hopper anymore.", None),
    (5, "Recommended", "Would buy again.", None),
    (5, "Reliable feeding times", "Meals come out exactly on schedule.", None),
    (4, "Nice design", "Looks good in the kitchen.", None),
    (5, "Fast delivery", "Arrived in two days.", None),
    (5, "Great product", "Makes mornings easier.", None),
    (4, "Does what it says", "No surprises.", None),
    (5, "Peace of mind", "Long work days are fine for the cat now.", None),
    (4, "Good value", "Cheaper than similar feeders.", None),
    (3, "Jams with bigger kibble", "Works with small kibble only.", "T6"),
],
"PS-CAR-005": [
    (2, "Zipper broke in a month", "The main zipper split after about 4 weeks of vet trips.", "I5"),
    (1, "Cat escaped", "After two months the zipper split open at the vet and my cat got out.", "I5"),
    (3, "Comfortable, weak zipper", "Straps are comfy and the window is great. But the zipper already catches and separates.", "I5"),
    (2, "Zip came off the track", "The zip slider came off on one side. Can't close the front properly anymore.", "I5"),
    (2, "Teeth separating", "The zipper teeth separate behind the slider. Had to tie it shut with a cable tie.", "I5"),
    (3, "Needs a better zip", "Love the design, but the zipper feels cheap and already started splitting.", "I5"),
    (4, "Good backpack, check the zip", "Very comfortable for hiking with my cat. The zip started splitting at the corner after a few months, I fixed it with pliers.", "I5"),
    (5, "Cat is calm inside", "She settles down as soon as we start walking.", None),
    (5, "Good ventilation", "Lots of air holes, she doesn't pant.", None),
    (4, "Comfortable straps", "Padded straps, easy on the shoulders.", None),
    (5, "The window is a hit", "She loves looking out of the bubble window.", None),
    (3, "Too small for a big cat", "My 7 kg Maine Coon barely fits.", "T5"),
    (3, "Snug for large cats", "Our big tom has to curl up tight in it.", "T5"),
    (5, "Fit under the seat on our flight", "No problems at the gate.", None),
    (5, "Easy to clean", "Wipe-clean inside, removable mat.", None),
    (4, "Sturdy base", "Doesn't sag with the cat inside.", None),
    (5, "Great for vet trips", "Much easier than the old plastic box.", None),
    (5, "Hiking with the cat", "We go on short trails every weekend now.", None),
    (4, "Good quality for the price", "Feels well made.", None),
    (5, "Love it", "Cute and practical.", None),
    (4, "Lightweight", "Easy to carry even when full.", None),
    (5, "Cat goes in by herself", "She treats it like a cave.", None),
    (5, "Great", "Exactly what we needed.", None),
    (4, "Chest strap is useful", "Keeps it stable when walking.", None),
    (5, "Fast delivery", "Came the next day.", None),
    (4, "Nice colour", "Looks better than in the photos.", None),
    (5, "Bought a second one", "One for each of our cats.", None),
    (4, "Good", "Happy with it.", None),
    (5, "Comfortable for both of us", "My back and the cat are both happy.", None),
    (2, "Smells of plastic", "Strong plastic smell for the first week.", None),
],
"PS-TOY-006": [
    (5, "Survived my lab", "Indestructible so far, 3 weeks of heavy chewing.", None),
    (5, "Treat slot keeps him busy", "Fill it with kibble and he's quiet for half an hour.", None),
    (2, "Lasted two days", "My pit bull chewed a chunk off on day two.", "T2"),
    (2, "Not for power chewers", "Pieces came off within a week, I took it away.", "T2"),
    (3, "Dog ignored it", "Not interested at all.", "T7"),
    (3, "Not interested", "She sniffed it once and went back to her old ball.", "T7"),
    (3, "Rubber smell", "Strong rubber smell at first.", None),
    (5, "Fun for fetch", "Bounces in random directions, he loves chasing it.", None),
    (5, "Great for a teething puppy", "Soothes her gums.", None),
    (4, "Good size", "Right size for our medium dog.", None),
    (5, "Floats", "Great at the lake.", None),
    (5, "Easy to clean", "Rinse and done.", None),
    (5, "Favourite toy", "Carries it everywhere.", None),
    (4, "Keeps her busy", "Good for rainy days.", None),
    (5, "Tough", "No marks after a month.", None),
    (5, "Bought three", "One for each room.", None),
    (4, "Good value", "Cheaper than similar toys.", None),
    (5, "Great with peanut butter", "Frozen with peanut butter it lasts ages.", None),
    (5, "Durable", "Still in one piece.", None),
    (4, "Nice", "Good toy.", None),
    (5, "Perfect for fetch", "Easy to throw far.", None),
    (5, "Calms him down", "Chewing it helps when he's anxious.", None),
    (4, "Solid", "Well made.", None),
    (5, "Great", "Dog loves it.", None),
    (5, "Long-lasting", "Two months and counting.", None),
    (4, "Good for medium dogs", "Too big for small dogs, perfect for ours.", None),
    (5, "Recommended", "Would buy again.", None),
    (5, "Worth it", "Best toy we've bought.", None),
    (4, "Does the job", "Keeps him off the furniture.", None),
],
"PS-FOD-007": [
    (2, "Bag arrived torn", "The 12 kg bag was ripped at the bottom and kibble was all over the delivery box.", "I6"),
    (3, "Food great, packaging not", "My dog loves it. Second order in a row where the bag was split on arrival.", "I6"),
    (2, "Spilled kibble", "The outer box was fine, but the bag inside was torn and about a third had spilled out.", "I6"),
    (1, "Torn bag", "The bag was torn on one side, food exposed to air. Not acceptable for food.", "I6"),
    (3, "Pack it better please", "The bag was punctured during delivery. Taped it up, but please use a stronger bag or an extra box.", "I6"),
    (4, "Good food, damaged bag", "Shiny coat after a month. The bag had a hole when it arrived though.", "I6"),
    (5, "Picky eater loves it", "First food he finishes every time.", None),
    (5, "Better digestion", "Firmer stools since switching, no more itching.", None),
    (5, "Shiny coat", "Visible difference after three weeks.", None),
    (4, "Pricey but worth it", "Not cheap, but she's healthier.", None),
    (3, "Expensive", "Good food, but too expensive for a big dog.", None),
    (2, "Upset stomach", "Diarrhoea for a few days when switching. Mix it in slowly.", None),
    (5, "No grain, no allergy", "His skin cleared up.", None),
    (5, "Good ingredients", "Real chicken first on the list.", None),
    (4, "Dog likes it", "Eats it without fuss.", None),
    (5, "Energy for a working dog", "Our collie is full of energy.", None),
    (5, "Subscription is handy", "Never run out now.", None),
    (5, "Good kibble size", "Easy to chew for our older dog.", None),
    (4, "Good food", "Happy with it.", None),
    (5, "Itching stopped", "Two weeks and no more scratching.", None),
    (5, "Second bag", "Will keep buying.", None),
    (4, "Dog eats it all", "Bowl is empty every time.", None),
    (5, "Vet approved", "Our vet liked the ingredient list.", None),
    (5, "Best food so far", "Tried many, this one works.", None),
    (4, "Good value for the quality", "Fair price for what you get.", None),
    (5, "Healthy weight", "He lost the extra kilos.", None),
    (5, "Love it", "Great food.", None),
    (3, "Delivery took long", "Food is good, delivery took 8 days.", None),
    (5, "Clean ingredients", "No fillers.", None),
    (4, "Fine", "Does the job.", None),
    (5, "My senior dog eats again", "She was losing interest in food, not anymore.", None),
    (5, "Great", "Recommended.", None),
],
"PS-SCR-008": [
    (3, "A bit wobbly", "Wobbles when my big cat jumps on it.", "T1"),
    (2, "Wobbles", "The base is too light, it tips when she scratches hard.", "T1"),
    (3, "Sisal sheds", "Bits of sisal everywhere after two weeks.", None),
    (5, "Cat stopped scratching the sofa", "Within a week she switched to the post.", None),
    (5, "Tall enough", "80 cm is perfect, she can fully stretch.", None),
    (5, "Easy assembly", "Five minutes, no tools.", None),
    (4, "Good quality", "Sisal feels tight and strong.", None),
    (5, "Cats love it", "Both cats use it daily.", None),
    (5, "Saved my couch", "Finally.", None),
    (4, "Nice", "Looks good in the hallway.", None),
    (5, "Fine for my kitten", "She climbs it all day.", None),
    (5, "Great", "Exactly as described.", None),
    (4, "Looks good", "Neutral colour, fits our flat.", None),
    (5, "Worth it", "Cheaper than a new sofa.", None),
    (5, "Second one", "Bought one for upstairs.", None),
    (4, "Good value", "Fair price.", None),
    (5, "Perfect", "Cat uses it every morning.", None),
    (5, "Daily use", "Still looks new after a month.", None),
    (4, "Fine", "Does the job.", None),
    (5, "Quick delivery", "Two days.", None),
    (5, "Love it", "Great post.", None),
    (4, "Solid", "Well made.", None),
    (5, "Recommended", "Would buy again.", None),
    (5, "Cat approved", "She ignores the furniture now.", None),
    (4, "Does the job", "Simple and effective.", None),
    (5, "Great post", "Tall and sturdy enough for our cat.", None),
],
}


def main(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(42)
    start = date(2026, 3, 1)

    rows = []
    for sku, reviews in R.items():
        for rating, title, text, label in reviews:
            rows.append({"sku": sku, "rating": rating, "title": title, "text": text, "label": label,
                         "date": start + timedelta(days=rng.randrange(0, 233))})
    rows.sort(key=lambda r: (r["date"], r["sku"], r["title"]))
    for i, r in enumerate(rows, 1):
        r["review_id"] = f"R{i:03d}"

    with open(out_dir / "products.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sku", "product_name", "page_claims"])
        w.writerows(PRODUCTS)

    with open(out_dir / "reviews.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["review_id", "sku", "date", "rating", "title", "text"])
        for r in rows:
            w.writerow([r["review_id"], r["sku"], r["date"].isoformat(), r["rating"], r["title"], r["text"]])

    with open(out_dir / "ground-truth.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "type", "sku", "accepted_themes", "description", "review_count", "review_ids"])
        for kind, table in (("planted_issue", ISSUES), ("trap", TRAPS)):
            for key, (sku, themes, desc) in table.items():
                ids = [r["review_id"] for r in rows if r["label"] == key]
                w.writerow([key, kind, sku, themes, desc, len(ids), "|".join(ids)])

    per_sku = {sku: len(v) for sku, v in R.items()}
    print("reviews:", len(rows), "| per product:", per_sku)
    print("planted reviews:", sum(1 for r in rows if r["label"] in ISSUES),
          "| trap reviews:", sum(1 for r in rows if r["label"] in TRAPS))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
