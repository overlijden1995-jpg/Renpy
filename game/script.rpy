label start:
    jump p17_cold_open


label p17_cold_open:
    $ coldopen_labour = False
    $ coldopen_water = False
    $ coldopen_silence = False
    $ water = 1

    # 1. Wasteland road.
    scene black
    "Dawn came the colour of old brass. Dust moved in low sheets over the wasteland road. He had walked six days through wire fences without settlements, past a dry trough, and one crow too tired to argue."
    "His canteen was empty, except for the mouthful he had stopped calling a drink. It was insurance against a worse hour. Every hour lately had volunteered."
    "He had no name he intended to give."

    # 2. Perimeter wall.
    show mc idle neutral at left
    show tory idle neutral at right
    "The wall rose ahead: sheet steel, packed earth, and timber braced against an old wound. A woman watched from the gate platform with a bolt-action crossbow across her chest."
    "Tory" "That's far enough."
    "It was not a shout. The crossbow did not rise. Her attention did."

    # 3. Open hands.
    "He stopped. Dust kept going. He opened his hands where she could see them."
    "His torn sleeve showed the chitin on his left arm from wrist to elbow. Tory looked at it, then at his face. She made no remark and did not tighten her aim."
    "The bolt stayed in its groove. At this gate, that passed for mercy."

    # 4. Scanner triage.
    hide tory
    show denice work neutral at right
    "A sally port opened beside the main gate. Denice came out with a handheld scanner, already looking at its display rather than at him."
    "He drew breath to answer the question Tory had not asked."
    "Denice" "Hold still."
    "The scanner clicked near his shoulder, clicked again near his wrist. A pale line travelled across its screen. Denice waited for it to settle."
    "Denice" "He's clean."
    "She called it back, then checked the scanner again. Whatever else it told her, she kept to herself."

    # 5. Tory's measure.
    hide denice
    show tory idle neutral at right
    "Tory" "Clean isn't the same as useful."
    "Behind her, someone shifted a barrier. The crossbow remained exactly where it had been."

    # 6. Sophia's slate.
    hide sophia
    show sophia work neutral at center
    "Sophia arrived with a slate and a pencil stub. She wrote before she looked at him. The pencil stopped while she took his measure, then moved again."
    "Sophia" "One body. One ration. One bed. One problem."
    "Sophia" "That is what you cost before breakfast. It is not an accusation. It is arithmetic."
    "She was not unkind. She gave numbers the same care another person might give a bandage."

    # 7. Alice and the cistern.
    hide sophia
    show alice work neutral at center
    "Alice came up from the cistern with two empty buckets knocking against her legs. She set them down, frowned at the pump, and picked them up again."
    "Alice" "Pump's been dead eleven days. Eleven. I keep oiling the hinge because the alternative is admitting I don't know which part is dying this time."
    "She looked at his canteen, not for long. Her fingers closed around one bucket handle instead."

    # 8. The only choice.
    menu:
        "Offer labour.":
            $ coldopen_labour = True
            "He nodded toward the pump, then the wall."
            "You" "I can work. Carry, dig, haul. I learn quickly."
            "Tory" "Work first. Speeches later."
            "Alice pointed him toward the gate with her free hand. Not a welcome. A job waiting."

        "Hand over the canteen's last mouthful. (Costs 1 water.)":
            $ coldopen_water = True
            $ water -= 1
            "He unslung the canteen and held it out. Alice took it, heard the small remaining movement inside, and did not drink."
            "Alice" "One mouthful. That's one mouthful the cistern doesn't have."
            "She passed the canteen through the sally port with elaborate care, as if it were full."

        "Say nothing and wait.":
            $ coldopen_silence = True
            "He kept his hands open and waited. Dust found the creases of his coat. Nobody filled the silence for him."
            "Tory watched him for three breaths. Denice's scanner clicked again. Sophia turned the slate over and wrote nothing."
            "At last Tory lowered the crossbow by an inch. Not trust. A measurement completed."

    # 9. Probation at the gate.
    hide tory
    hide alice
    hide denice
    show tory idle neutral at right
    $ probation = True
    "The gate opened wide enough for one person. Metal complained. Nobody called it safe inside or promised breakfast."
    "Tory" "Probation. No ration until you earn one. Knife."
    "He unfastened the sheath and offered it hilt first. Tory took the knife, counted the people behind the wall with one glance, and stepped aside."
    "Tory" "One in. Same one comes out if this goes wrong."

    # 10. Interior.
    scene black
    show sophia work neutral at right
    show alice work neutral at left
    "Inside smelled of wet ash, old canvas, and stretched beans. Sophia sat at a crate and opened the slate to a clean column."
    "Sophia" "Stranger. Gate entry, dawn. Probationary labour. Knife held by Tory. No ration issued."
    "She added a small mark beside the water column without explaining it."
    "Across the yard, Alice was sorting dry fittings by size. She pointed at an empty bunk beneath a patched awning without looking up."
    "Alice" "That one. Blanket's thin, roof mostly works, and if you touch my water jars I will know before you do."

    # 11. Night at the pump.
    scene black
    show mc idle neutral at left
    "Night put the wall in shadow. He sat beside the dead pump with a hooded lantern, close enough to see flaked paint and the clean ring where a bolt had been removed."
    "He did not fix it. He did not take it apart or find a miracle in the pipe. He looked at the dark joints and the handle polished by other people's hands."
    "Eleven days, Alice had said. The number stayed with him longer than the scanner's clean result."

    # 12. Day 1.
    scene black
    "Dawn found dust on the pump and the first work bell ringing. A bucket struck stone behind him. Day one began without asking whether he was ready."
    jump colony_loop
