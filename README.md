# Debian 13 backports 内核 + BBRv3（实验性移植）

本仓库是 **Debian `linux-source-7.2` / `7.2.9-1~bpo13+1` 完整源码快照**，加上从 Google BBR `v3` 分支移植的 BBRv3 和对应 TCP 核心改动。

> **不是 Debian 或 Google 官方发布的定制内核。**
> 相关 TCP 文件已通过目标文件编译检查；原 VPS 的完整构建因换机而主动停止，尚未完成最终链接、安装、启动或稳定性测试。请勿把源码提交或算法名 `bbr` 当作验证成功。

## 下载

公开仓库可直接下载，无需 SSH 密钥：

```sh
git clone --depth=1 https://github.com/Qing75/debian13-bbrv3.git
cd debian13-bbrv3
```

仓库导入的是源码快照，不包含 Linux 历年的完整 Git 历史，也不包含源码压缩包、编译产物、VPS 日志或本机 SSH 密钥。
原内核的 `README`、`COPYING` 和 `LICENSES/` 均保留。

## 源码来源

- Debian：`linux-source-7.2`，版本 `7.2.9-1~bpo13+1`，来自 `trixie-backports` 的已认证 APT 索引。
- Debian 源码压缩包 SHA256：
  `29f9eafc0826dcc54ff9ace28a326c265f4752c22f57a87027446b5353451f25`
- Google BBR：https://github.com/google/bbr/tree/v3
- 固定提交：`90210de4b779d40496dee0b89081780eeddf2a60`，其内核基线为 Linux 6.13.7。
- 本地构建目标：`7.2.9-deb13-bbrv3`，amd64/x86_64。

仓库已应用移植补丁，**克隆后不要再次应用** `local-build/bbrv3-debian-7.2.9.patch`。该文件用于审阅，以及在相同 Debian 原始源码上复现修改。

## 本地构建文件

| 文件 | 用途 |
|---|---|
| `local-build/debian13-amd64-bbrv3.config` | 从 Debian 官方 amd64 配置调整得到的构建配置 |
| `local-build/bbrv3-debian-7.2.9.patch` | 以 Debian 原始源码为基准的 BBRv3 移植补丁 |
| `local-build/PORTING.md` | 接口兼容处理、功能限制及验证状态 |
| `local-build/verify-bbrv3.py` | 启动新内核后，检查新 TCP 连接自报的 BBR 版本 |

配置未主动裁剪硬件驱动，但关闭了调试信息、BTF 和 Rust，因此部分 BTF/eBPF 工具和 Rust 驱动不可用。发行版证书引用已清空；模块签名保留为本地生成的密钥，并非 Debian Secure Boot 签名。

## 编译 Debian 二进制包

推荐在 Debian 13 amd64 上构建，建议至少 4 核、8 GiB 内存和 25～30 GiB 可用磁盘。资源较少也可能构建，但不能保证空间、时间或内存足够。

安装依赖（会安装构建工具，不会安装新内核）：

```sh
sudo apt-get update
sudo apt-get install --no-install-recommends \
  build-essential bc bison flex libssl-dev libelf-dev libdw-dev \
  rsync debhelper cpio kmod xz-utils zstd python3 git
```

在仓库根目录执行：

```sh
cp local-build/debian13-amd64-bbrv3.config .config
make LOCALVERSION= olddefconfig
make -s LOCALVERSION= kernelrelease
```

预期输出为 `7.2.9-deb13-bbrv3`。随后根据机器内存选择并行数；下面保守地使用两个任务：

```sh
JOBS=2
make -j"$JOBS" LOCALVERSION= bindeb-pkg \
  DPKG_FLAGS="-j$JOBS" \
  KDEB_PKGVERSION='7.2.9-1~bpo13+1+bbrv3.1'
```

`DPKG_FLAGS` 用来覆盖内核打包规则内部默认的 `dpkg-buildpackage -j1`。
生成的 `.deb` 位于仓库的上一级目录。以上命令不包含安装、修改 GRUB 或重启。
如果在资源紧张的生产 VPS 上编译，应另行设置 CPU/内存限制和磁盘空间保护；这里的手动编译命令不含原 VPS 上的资源监督器。

**不要直接运行 `dpkg -i *.deb`。** 除内核镜像和可选头文件外，构建还可能生成不需要替换的 `linux-libc-dev` 包。安装前检查精确包名、原内核回退入口和 Secure Boot 状态。

## 启动后的版本验证

安装与重启应单独审核，并保留原官方内核。启动后可检查：

```sh
uname -r
modinfo -F version tcp_bbr
python3 local-build/verify-bbrv3.py
```

验证脚本在回环地址上创建新 BBR 连接，读取扩展 `TCP_CC_INFO` 中的 `bbr_version`，不修改全局 sysctl，不向外发送流量。
该移植应报告版本 `3`；仅在 `ss` 或 sysctl 中看到 `bbr` 不足以区分版本。
版本检查不等于功能、稳定性或性能测试。BBRv3 也不保证所有网络线路都会提速。

## 维护和许可

这是固定版本源码；发布到 GitHub 不会自动获得后续 Debian 安全修复，后续更新需要重新移植、编译及测试。
请保留源码各文件的版权和许可标识。Linux 内核许可见 `COPYING`、`LICENSES/`；BBR 文件保留了 Google 作者及双重许可标识。
