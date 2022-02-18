# Tsagaglalal

> Tsagaglalal [sa-ga-gla-la], or “She who watches” in the Wasco-Wishram language.

![alt text](https://www.freevector.com/uploads/vector/preview/3857/FreeVector-Tsagaglalal.jpg)

A V Systems NFT token indexer service.

This lean and effcient service watches the NFT transactions on preset contracts, saves them to a local database to be consumed over the API later on.
Service is architected to be able to serve hundrets, if not thousands, of simultaneous NFT token contracts but for the moment it's only used by the [Felix project](https://saveaword.com).

## Config

Edit the ```conf.yaml``` file, write down all NFT token contracts you'd like to be watched.

## API

###  [GET] /associatedtokens/{contract_id:str}/{address:str}

Query db for which token id's are associated with some V Systems address.

Retuns an array:

```
[
	"TWtXWsFec5sxxYWrS92wTn6zcKMJtRPUEW4naqWZM",
	"TWtXWsFec5sxxYWrS92wTn6zcKMJtRPUEW5Brt66J",
	"TWtXWsFec5sxxYWrS92wTn6zcKMJtRPUEW5PctDfk",
	"TWtXWsFec5sxxYWrS92wTn6zcKMJtRPUEW5S3XYr3",
	"TWtXWsFec5sxxYWrS92wTn6zcKMJtRPUEW5Ye7kDz",
	"TWtXWsFec5sxxYWrS92wTn6zcKMJtRPUEW7h4jWJ5",
	"TWtXWsFec5sxxYWrS92wTn6zcKMJtRPUEW8FCUnen",
	"TWtXWsFec5sxxYWrS92wTn6zcKMJtRPUEW8Jygz81",
	"TWtXWsFec5sxxYWrS92wTn6zcKMJtRPUEW8SzgkB6",
	"TWtXWsFec5sxxYWrS92wTn6zcKMJtRPUEW8X51Fsk",
	"TWtXWsFec5sxxYWrS92wTn6zcKMJtRPUEW8eUHigP",
	"TWtXWsFec5sxxYWrS92wTn6zcKMJtRPUEW8mstzFN",
	"TWtXWsFec5sxxYWrS92wTn6zcKMJtRPUEW8yd51md",
	"TWtXWsFec5sxxYWrS92wTn6zcKMJtRPUEW9GaitCw",
	"TWtXWsFec5sxxYWrS92wTn6zcKMJtRPUEW9ReGSf7",
	"TWtXWsFec5sxxYWrS92wTn6zcKMJtRPUEW9but4qM",
	"TWtXWsFec5sxxYWrS92wTn6zcKMJtRPUEW9dNxQnB",
	"TWtXWsFec5sxxYWrS92wTn6zcKMJtRPUEW9pVUkpJ"
```