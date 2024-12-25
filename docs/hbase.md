## HBase Configuration and Usage Guide for F1 Data Analysis

This document outlines HBase configuration and usage for the F1 data analysis platform, where it serves as a scalable NoSQL database for storing large volumes of structured data like telemetry and race statistics.

**Architecture Overview**

HBase employs a distributed architecture for scalable and reliable data storage.

| Component        | Role & Responsibilities                                                                                                                                                                                                                                                                                          | EMR Node Type |
|-----------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| **Master Server** | Coordinator: Region assignment, schema changes, load balancing, monitoring, garbage collection, region splitting management.                                                                                                                                                                                    | `m7g.xlarge`   |
| **Region Servers**| Data handlers: Serving read/write requests, data storage in HFiles on HDFS, MemStore management (in-memory write buffer), compaction, region splitting execution and reporting. Each server manages multiple regions.                                                                                           | `r7i.xlarge`   |
| **ZooKeeper**     | Coordination service: Cluster state management, distributed synchronization, configuration storage, Master leader election, failure detection.                                                                                                                                                              | Master Node   |

**Storage Architecture**

HBase manages data in a hierarchical manner:

*   **Regions:** Fundamental units of data distribution, containing sorted row ranges. Regions split automatically as they grow. The Master assigns regions to RegionServers, considering load and data locality.
*   **Storage Implementation:**
    *   **MemStore:** In-memory write buffer for fast writes, sorted by row key, flushed to disk as HFiles when thresholds are met. Each column family has its own MemStore.
    *   **HFiles:** Immutable, persistent storage on HDFS. Organized for efficient lookups. Compaction merges smaller HFiles to improve read performance.
    *   **Write Ahead Log (WAL):** Durable log recording data changes before MemStore writes, ensuring data durability in case of failures. Used for recovery by replaying un-flushed data.

**Configuration Management**

Proper configuration is crucial for HBase performance. Key configuration files are located in `/etc/hbase/conf/` and `/etc/hadoop/conf/`.

| File             | Purpose                                                                                                                                                                        | Key Examples                                                                                                                                 |
|------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| `hbase-site.xml` | Primary HBase configuration: cluster settings, performance tuning, security, integration with other services.                                                                 | `hbase.rootdir` (HDFS root), `hbase.zookeeper.quorum` (ZooKeeper addresses), `hbase.cluster.distributed` (true), MemStore/cache settings. |
| `hdfs-site.xml`  | HDFS configuration: replication factor, block size, HDFS-specific performance settings.                                                                                           | `dfs.replication` (HDFS replication factor), `dfs.blocksize`.                                                                                |
| `regionservers`  | Lists hostnames of all RegionServers in the cluster, used by the Master.                                                                                                      | List of RegionServer hostnames.                                                                                                               |

**Critical Configuration Areas:**

*   **Memory Management:**
    *   **Region Server Heap:**  Allocate a significant portion of RAM (e.g., for `r7i.xlarge` with 32GB RAM).
    *   **MemStore Size (`hbase.hregion.memstore.flush.size`):** Balances frequent small flushes with memory consumption.
    *   **Global MemStore Limit (`hbase.regionserver.global.memstore.size`):**  Upper limit for total MemStore usage, triggers flushes.
    *   **Block Cache (`hfile.block.cache.size`):** Proportion of heap for caching frequently accessed data blocks, crucial for read performance. Tune eviction policies (`hbase.blockcache.low`, `hbase.blockcache.high`).

**Configuration Challenges & Solutions:**

| Challenge                       | Solution                                                                                                                                                                                                                                 |
|---------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Incompatible HDFS Replication  | Modified `hdfs-site.xml` and `hbase-site.xml` to set `dfs.replication` to 2. Restarted NameNode and HBase Master. Manually adjusted replication for existing HBase data.                                                                  |
| Region Server Startup Failures  | Manually restarted RegionServer processes and addressed under-replicated blocks in HDFS.                                                                                                                                                 |
| WAL File Blocking Replication | Temporarily disabled WALs, adjusted the replication factor, and then re-enabled WALs.                                                                                                                                                       |

**Operational Challenges & Solutions:**

| Challenge                       | Solution                                                                                                                                            |
|---------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| DataNode Restart on Master Node | Expected error, DataNode should not run on the master in EMR.                                                                                       |
| Under-Replicated Blocks         | Monitored replication status using `hdfs dfsadmin -report` and `hdfs fsck /`, and waited for replication to complete. |

**Conclusion**

Understanding HBase architecture and configuration is essential for effectively managing and optimizing its performance within the F1 data analysis platform. Configuration, data modeling, and operational practices are tailored to the project's specific needs to ensure a robust, scalable, and efficient data storage solution.
