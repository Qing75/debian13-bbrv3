# Debian 13 cloud-amd64 + BBRv3 源码

这是 `cloud-bbrv3` 分支：**Debian backports 7.2.9 源码 + 同版本官方 cloud-amd64 配置 + Google BBRv3 移植**。

本次只提供源码及配置，**未编译、安装或启动本分支的 cloud 内核**。原来的通用 amd64 版本仍保留在 `main` 分支；本分支不使用它的禁用 BTF/Rust 配置。

## 下载

```sh
git clone --depth=1 --branch cloud-bbrv3 \
  https://github.com/Qing75/debian13-bbrv3.git
cd debian13-bbrv3
```

BBRv3 修改已经应用，**不要再次应用补丁**。仓库是完整源码快照，不包含编译产物、源码压缩包、SSH 密钥或原 VPS 的日志。

## 什么是 cloud 内核

Debian 的 `amd64` 和 `cloud-amd64` 共用 Linux 源码，主要区别在于构建配置。这里使用官方 **7.2.9 cloud-amd64 配置**，不是给旧通用配置改名，也没有运行 `localmodconfig` 或按原 VPS 硬件重新裁剪驱动。

保留官方 cloud 配置中的虚拟化驱动、BPF、**BTF、模块 BTF 和 Rust**。cloud 配置本身覆盖的硬件范围小于通用 amd64 配置，不应当作所有物理服务器的通用替代品。

## 来源与版本边界

本次刷新并核对 `trixie-backports` 已认证 APT 索引得到：

| 项目 | 版本 |
|---|---|
| Debian 源码包 `linux-source-7.2` | `7.2.9-1~bpo13+1` |
| 官方配置包 `linux-config-7.2` | `7.2.9-1~bpo13+1` |
| 配置包中的 cloud 配置 | `config.amd64_none_cloud-amd64.xz` |
| 已发布的 `linux-image-cloud-amd64` 元包 | `7.2.6-1~bpo13+1` |
| 本地目标内核标识 | `7.2.9-deb13-cloud-bbrv3` |

**最新可用源码/配置的版本，不等于已经发布的签名 cloud 镜像版本。**本分支按前者 7.2.9 制作；不是声称 Debian 已发布 7.2.9 签名 cloud 镜像，也不是 Debian 13 stable 默认的 6.12 系列。这里的“最新”仅指本次核对时可用的 backports 源码/配置，不保证未来保持最新。

- 源码压缩包 SHA256：`29f9eafc0826dcc54ff9ace28a326c265f4752c22f57a87027446b5353451f25`
- 官方 cloud 配置（解压后）SHA256：`7507099cdcba1b1477078222b31fb1b13d8be1f2b9e20c411939e7a0cf91f484`
- Google BBR v3 固定提交：`90210de4b779d40496dee0b89081780eeddf2a60`，其基线为 Linux 6.13.7。
- 完整输入记录见 `local-build/SOURCES.json`；TCP 接口适配见 `local-build/PORTING.md`。

## 本地文件

| 文件 | 用途 |
|---|---|
| `local-build/debian13-cloud-amd64.official.config` | 官方原始 cloud 配置，未修改，用于追溯和对比 |
| `local-build/debian13-cloud-amd64-bbrv3.config` | 本分支使用的 cloud 构建配置 |
| `local-build/bbrv3-debian-7.2.9.patch` | 针对原始 Debian 7.2.9 源码的完整 BBRv3 移植补丁 |
| `local-build/check_cloud_config.py` | 检查保存的配置，或检查 olddefconfig 后的 `.config` |
| `local-build/test_cloud_config.py` | 配置静态测试，不编译内核 |
| `local-build/verify-bbrv3.py` | 启动后在回环 TCP 连接中验证 BBR 自报版本 |

相对于官方 cloud 配置，只明确修改四个选项：

1. `CONFIG_LOCALVERSION="-deb13-cloud-bbrv3"`，区分官方及通用内核。
2. `CONFIG_MODULE_SIG_KEY="certs/signing_key.pem"`，构建时生成本地模块签名密钥。
3. `CONFIG_SYSTEM_TRUSTED_KEYS=""`，不依赖 Debian 构建环境中的证书文件。
4. `CONFIG_MODULE_SIG_ALL=y`，安装模块到打包目录时使用上述本地密钥签名。

保留官方的 `CONFIG_LOCALVERSION_AUTO=n`。本地模块签名**不是官方 Secure Boot 签名**；仓库不包含任何签名私钥。

BBR 保持模块形式，仍使用算法名 `bbr`。官方编译默认值 `cubic` / `fq_codel` 保持不变；源码和构建过程不会自动更改运行系统的 sysctl。若要使用 BBR/fq，应在实际安装启动后另行启用。

## 仅检查源码配置

以下命令不编译、不安装内核：

```sh
python3 local-build/check_cloud_config.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s local-build -p 'test_cloud_config.py' -v
```

## 在另一台机器构建（可选）

不要在原来的 2 核/2 GiB 生产 VPS 上重新构建。建议 Debian 13 amd64 构建机，至少 8 GiB 内存、40 GiB 可用磁盘，并按实际内存选择并行数。本配置保留调试信息以生成 BTF，构建磁盘需求比之前关闭调试信息的通用配置更高。

依赖安装示例（只在构建机上执行）：

```sh
sudo apt-get update
sudo apt-get install --no-install-recommends \
  build-essential bc bison flex libssl-dev libelf-dev libdw-dev \
  rsync debhelper cpio kmod xz-utils zstd python3 git pahole \
  rustc rust-src bindgen clang llvm libclang-dev
```

先检查工具链，再配置：

```sh
make rustavailable
cp local-build/debian13-cloud-amd64-bbrv3.config .config
make LOCALVERSION= olddefconfig
python3 local-build/check_cloud_config.py .config
make -s LOCALVERSION= kernelrelease
```

预期内核标识为 `7.2.9-deb13-cloud-bbrv3`。**若检查发现 BTF、模块 BTF 或 Rust 被关闭，先修复工具链依赖，不要直接继续构建。**Rust 构建要求及发行版包配置见 `Documentation/rust/quick-start.rst`。保存配置中的编译器版本字段来自 Debian 构建机，会在 olddefconfig 时按你的实际工具链更新。

然后构建 `.deb`，不安装：

```sh
JOBS=2  # 按构建机资源调整
make -j"$JOBS" LOCALVERSION= bindeb-pkg \
  DPKG_FLAGS="-j$JOBS" \
  KDEB_PKGVERSION='7.2.9-1~bpo13+1+cloudbbrv3.1'
```

产物在源码目录的上一级。保留调试信息时可能额外产生较大的 `-dbg` 包。
**不要直接执行 `dpkg -i *.deb`**，尤其不要无意替换 `linux-libc-dev`；安装、Secure Boot 处理、引导菜单变更和重启应单独确认，并保留原内核回退入口。

## 验证边界

- 本分支完成的是源码、补丁和 cloud 配置的静态检查；没有进行 cloud 配置下的编译、链接或启动验证。
- 此前相同 TCP 移植的通用配置版本，已由用户在另一台机器构建，并在原 VPS 安装启动；模块和实际 TCP 连接均报告 BBR 版本 3。**这不等于本 cloud 分支已通过构建或运行验证。**
- 日后启动 cloud 内核后，可用 `uname -r`、`modinfo -F version tcp_bbr` 和 `python3 local-build/verify-bbrv3.py` 检查。
- BTF 是否可用应检查 `/sys/kernel/btf/vmlinux`；不能仅凭保存配置宣称相关 systemd/BPF 功能已恢复。
- BBR 版本检查不等于损失、重排、ECN、长期稳定性或性能测试，也不保证所有线路提速。

## 维护与许可

这是固定版本的本地移植，**不是 Debian 或 Google 官方定制内核**。GitHub 源码不会自动获得新的 Debian 安全补丁，后续需要更新、重新移植和验证。

原始 `README`、`COPYING`、`LICENSES/` 及源码版权标识均保留；BBR 文件保留其作者和许可标识。
