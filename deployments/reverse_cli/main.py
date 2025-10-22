import sys

def main():
    try:
        s = input().strip()
    except EOFError:
        s = ''
    print(s[::-1])

if __name__ == '__main__':
    main()
