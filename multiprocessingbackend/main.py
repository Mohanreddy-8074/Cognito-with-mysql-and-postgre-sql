import asyncio

async def print_numbers():
    for i in range(1, 7):
        await asyncio.sleep(1)
        print(f'Number: {i}')

async def print_letters():
    for letter in ['M', 'O', 'H', 'A', 'N', 'K']:
        await asyncio.sleep(1)
        print(f'Letter: {letter}')

async def main():
    await asyncio.gather(
        print_numbers(),
        print_letters()
    )

if __name__ == "__main__":
    asyncio.run(main())

print("Both async tasks completed")

