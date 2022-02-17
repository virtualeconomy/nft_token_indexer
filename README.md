# Tsagaglalal

> Tsagaglalal, or “She who watches” in the Wasco-Wishram language.

![alt text](https://www.freevector.com/uploads/vector/preview/3857/FreeVector-Tsagaglalal.jpg)

A V Systems NFT token indexer service.

## API

###  [GET] /associatedtokens/{contract_id:str}/{address:str}

Query db for which token id's are associated with some V Systems address.

Retuns an array:

```
[
	0, 3, 5, 6,	7, 26
]
```