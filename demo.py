from loguru import logger


@logger.catch
def test():
    s = 1 / 0
    print(s)


test()

print(2)

print(''.upper())
