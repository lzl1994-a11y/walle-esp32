param([string]$Python = "python", [string]$Cxx = "g++")
$ErrorActionPreference = "Stop"
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    New-Item -ItemType Directory -Path build/host-tests -Force | Out-Null
    foreach ($test in @("test_audio_capture", "test_i2s_playback", "test_cdc_transport", "test_control_regressions", "test_pin_map")) {
        & $Python -B "tests/$test.py"
        if ($LASTEXITCODE -ne 0) { throw "$test failed" }
    }
    & $Python -B tools/test_camera_stream_protocol.py
    if ($LASTEXITCODE -ne 0) { throw "Camera/NETCFG protocol test failed" }
    $common = @("-std=c++17", "-Wall", "-Wextra", "-Werror", "-Itools/serial_output_test", "-Icomponents/walle_display/src")
    $cases = @(
        @{Name="test_serial_output"; Sources=@("tools/test_serial_output.cpp")},
        @{Name="test_control_input"; Sources=@("tools/test_control_input.cpp", "components/walle_display/src/adapters/input/SerialInputPort.cpp")},
        @{Name="test_host_network_screen"; Sources=@("tools/test_host_network_screen.cpp")},
        @{Name="test_eye_renderer"; Sources=@("tools/test_eye_renderer.cpp", "components/walle_display/src/domain/EyeRenderer.cpp")}
    )
    foreach ($case in $cases) {
        $sources = $case.Sources
        $executable = "build/host-tests/$($case.Name).exe"
        & $Cxx @common @sources -o $executable
        if ($LASTEXITCODE -ne 0) { throw "$($case.Name) compilation failed" }
        & "./$executable"
        if ($LASTEXITCODE -ne 0) { throw "$($case.Name) failed" }
    }
} finally { Pop-Location }
