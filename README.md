# 500strawberries
This tool allows you to decrypt and edit 100% orange juice savefile, allowing you to change anything (currency, items, stats, etc.) and place them back in the game, this also works with steam.

<img width="1700" height="957" alt="image" src="https://github.com/user-attachments/assets/aa83bf36-f282-497e-a409-5abfcc1aa24a" />

<img width="1700" height="957" alt="image" src="https://github.com/user-attachments/assets/b3e09052-74a0-4ead-a40d-5ea380238a3f" />

## Notes :
* This is for educational / research purposes only
* You are responsible for using this tool, anything that may happen (corrupted save, ban, data loss, etc) is your only responsibility !
* As this works with steam and overrides your save with the modified one, please do not use it to gain advantages over other players when playing online ! (I do not knnow how this game works for online mode but keep it fair ! And if you get banned / VAC banned it is your responsability)
* This was made as of `3.28.1.e87310a63-Windows.3003000.AMD.STEAM.RELEASE`.
* This may break over time, and this will not be updated, if you see this tool does not work and was last updated a long time ago, it is likely outdated

# Usage

1. Close steam
2. Start game manually from exe, you will get warning about using a local save file instead of steam, once in menu, close game
3. Go to `100 Orange Juice\save\[YOUR_ID]`
4. Pick the file corresponding to your slot, eg. `profile0.ojs`
5. Run `python main.py decrypt profile0.ojs`
6. If you want basic changes (stars, oranges, hours played, play count), run `python changes.py profile0.json`, you can edit the file to changes the wanted values. Otherwise you will have to find t he other stuff to edit yourself
7. Once done changing your save, run `python main.py encrypt profile0.json`, place the newly generated `profile0.ojs` back into the game directory replacing the old one (don't forget to make a backup !)
8. Start game manually, should show your new stats, if so, you can reopen steam and start from there so it overrides your steam save

Note: you can technically skip the steam steps and do everything without closing steam, this is just to prevent accidental corruption

# Nerdy stuff

ohhh cringe..
this is for people interested in expanding / updating the tool, giving research content

## Save file structure

| Offset   | Size | Name                     |
|----------|------|--------------------------|
| 0x000    | 4    | CRC32                    |
| 0x004    | 255  | ChaCha Key Material      |
| 0x103    | 4    | Payload Size             |
| 0x107    | 64   | HMAC Key                 |
| 0x147    | 12   | ChaCha Nonce Seed        |
| 0x153    | 32   | ChaCha Key               |
| 0x173    | 4    | Decompressed Size        |
| 0x177    | 4    | Compressed Size (N)      |
| 0x17B    | N    | LZ4 Compressed JSON      |
| 0x17B+N  | 32   | HMAC Hex Digest          |

## Dumping from memory

Hook `0xC89680` and save onEnter's arg0 then on leave get size of array from pointer and read. Example frida script : 

```js
const mod = Process.getModuleByName('100orange.exe');
const base = mod.base;

Interceptor.attach(base.add(0xC89680), {
  onEnter: function(args) {
    this.bufferObj = args[0];
  },
  onLeave: function(retval) {
    const sizeFunc = new NativeFunction(base.add(0xC89690), 'uint64', ['pointer']);
    const size = sizeFunc(this.bufferObj);
    const dataPtr = ptr(retval);
    const jsonString = dataPtr.readUtf8String(size.toNumber());

    console.log(jsonString);
  }
});
```

<img width="2872" height="1550" alt="image" src="https://github.com/user-attachments/assets/823e5067-c950-4f6a-92d6-bae72cfa4d14" />

## Functions

### 0xC8BA00 — LZ4_decompress

```c
int LZ4_decompress(
    const void* src,        // compressed input buffer
    void* dst,              // output buffer (decompressed)
    uint32_t srcSize,       // compressed size (bytes)
    uint32_t dstCapacity    // max output size (bytes)
);
```
Return
* `int` → decompressed size
* `< 0` = error

### 0xC89680 — Buffer_Copy / memcpy wrapper
```c
void* BufferCopy(
    void* bufferObj         // internal buffer object
);
```

Return
- `void*` → pointer to raw buffer data

### 0xC896A0 — ReadSaveFile
```c
void* ReadSaveFile(
    const char* filepath,   // UTF-8 path
    void** outDataStruct    // pointer to data container
);
```

Arg details
* `*outDataStruct` → heap buffer pointer following this struct :

```c
struct {
    void *data_ptr;   // offset 0
    uint64_t size;    // offset 8
}
```

Return
* `void*` → internal buffer / file handle

### 0x2D1710 — ChaCha20_Block
```c
uint8_t* ChaCha20_Block(
    void* ctx,              // unknown / state
    const uint8_t constant[32],
    const uint8_t key[32],
    const uint8_t nonce[12],
    uint32_t counter
);
```

Return
* `uint8_t*` → pointer to 64‑byte keystream block

### 0x2D1A00 — MersenneTwister_Init
```c
void MT_Init(
    uint32_t* stateTable,   // [0]=index, [1..624]=state
    uint32_t warmupCount
);
```

Return
* `void`

### 0x2B4430 — MersenneTwister_Extract
```
uint32_t MT_Extract(
    uint32_t* stateTable
);
```

Return
* `uint32_t` → tempered RNG output

### 0x2D1CC0 — SHA256
```c
uint8_t* SHA256(
    void* ctx,              // internal SHA context
    const uint8_t block[64],
    void* bufferObj         // data buffer using fOAEP struct from above
);
```

Return
* `uint8_t*` → 32‑byte hash output

### 0xC88C10 — DecryptPayload
```c
void* DecryptPayload(
    void* cryptoHandle,     // output written here
    struct {
        uint8_t* data;      // encrypted input
        uint64_t size;      // input size
    }* inData,
    const uint8_t chachaConst[16]
);
```

Return
* `void*` → cryptoHandle / internal object

### 0xC8A620 — CRC32
```c
uint32_t CRC32(
    const uint8_t* data,
    uint64_t size,
    uint32_t seed
);
```

Return
* `uint32_t` → CRC value

# Credits

If you like this project, feel free to leave a star, and check out my other stuff. And if you use it, feel free to credit <3
