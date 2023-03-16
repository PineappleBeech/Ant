from ant.worker import Worker

def main():
    worker = Worker("test", "127.0.0.1", 6543)
    worker.run()

if __name__ == '__main__':
    main()