import subprocess


def run(a, b):
    outline = subprocess.run(
        ["sed", "-rf", "./fullsubber.sed"],
        input="{:b}#{:b}".format(a, b).encode("utf-8"),
        capture_output=True,
    ).stdout.decode("utf-8").strip().split("\n")[-1]
    return int(outline.split("#", 1)[0], 2)


for i in range(1024):
    for j in range(9, 10):
        assert run(i, j) == max(i - j, 0), (i, j)
