# Fast Folder Copier

A high-performance, multi-threaded folder copying tool built for large data transfers.

*DISCLAIMER: I hold credits only about the idea, the rest of the code was written by a local offline coding llm*

### Why is this better than normal Windows Copy-Paste?

| Feature                    | Windows Explorer Copy          | Fast Folder Copier                  | Advantage |
|---------------------------|--------------------------------|-------------------------------------|---------|
| Copy Method               | Single-threaded                | Multi-threaded (up to 64 threads)   | Much faster |
| Chunk Size                | Very small (~64 KB)            | Large chunks (128 MB)               | Better SSD speed utilization |
| Performance with Many Files | Slow                           | Excellent                           | Great for folders with thousands of files |
| Speed on Big Transfers    | Average                        | Often **2x to 4x faster**           | Saves hours on TB-level transfers |
| Real-time Progress        | Basic                          | Detailed (Speed, ETA, GB copied)    | Actually useful information |
| CPU & Disk Usage          | Low                            | High (designed for max performance) | Uses your hardware to its full potential |
| Reliability               | Can hang or slow down          | More consistent                     | Better for long transfers |
| Safety                    | Safe                           | **Safer** - Original files untouched | No risk of data loss during copy |

### Real-World Difference

- **Normal Windows copy** = One guy moving boxes slowly.
- **This tool** = 64 movers working together with huge carts.

Especially useful when:
- Moving large game folders
- Backing up photos/videos
- Transferring between SSD and HDD
- Copying folders with 100,000+ small files

**Important Note**:  
This tool **only copies**. It never deletes anything from your source folder. Your original files remain completely safe.
