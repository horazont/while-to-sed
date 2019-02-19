import subprocess


def run(a, b):
    return int(subprocess.run(
        ["sed", "-rf", "./fullsubber.sed"],
        input="#{:b}#{:b}".format(a, b).encode("utf-8"),
        capture_output=True,
    ).stdout.decode("utf-8").strip().split("\n")[-1].split("#", 1)[1], 2)


for i in range(16):
    for j in range(16):
        assert run(i, j) == max(i - j, 0), (i, j)
