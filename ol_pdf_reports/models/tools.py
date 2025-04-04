# Useful functions used by reports


def newline_to_br(text):
    return "<br/>".join([x.rstrip() for x in text.splitlines() if x.strip()]) if text else text
