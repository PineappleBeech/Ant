from ant.worker import Worker

def main():
    worker = Worker("test", 6543)
    worker.run()

if __name__ == '__main__':
    main()