def clean_text(text):
    fillers = ["uh", "um", "like", "actually", "you know"]

    for f in fillers:
        text = text.replace(f, "")

    return text.strip()