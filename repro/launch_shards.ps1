# 并行分片启动器：3 种 think 模式 × 3 个任务分片 = 9 个 worker
# 用法（在 repro 目录下）：
#     pwsh -File launch_shards.ps1
# 每个 worker 独立的 state / gather / 日志文件，互不覆盖；
# 中途停掉重跑会自动跳过已完成的 (任务, 方法)。

$ErrorActionPreference = 'Stop'
$py = 'C:\Users\13988\anaconda3\envs\CodeSteer\python.exe'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$shards = [ordered]@{
    's1' = 'game24,number_multiply,letters,gsm'
    's2' = 'MATH_geometry,MATH_cp,BoxNet1,blocksworld,BoxLift'
    's3' = 'big_bench_hard,path_plan,letters_sentence'
}

$procs = @()
foreach ($mode in @('off', 'strip', 'on')) {
    foreach ($s in $shards.Keys) {
        $env:THINK_MODE = $mode
        $env:REPRO_STATE_TAG = $s
        $env:REPRO_LOG = Join-Path $root "logs\llm_calls_$mode`_$s.jsonl"
        $out = Join-Path $root "logs\shard_$mode`_$s.log"
        $err = Join-Path $root "logs\shard_$mode`_$s.err.log"
        $p = Start-Process -FilePath $py `
            -ArgumentList @('-X', 'utf8', 'run_all.py', '--cap', '50', '--tasks', $shards[$s]) `
            -WorkingDirectory $root -NoNewWindow -PassThru `
            -RedirectStandardOutput $out -RedirectStandardError $err
        Write-Host ("start {0}/{1} pid={2}" -f $mode, $s, $p.Id)
        $procs += $p
        Start-Sleep -Milliseconds 700
    }
}

$procs | Wait-Process
Write-Host "all workers exited"
