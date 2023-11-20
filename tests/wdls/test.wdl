version 1.0

workflow test {
    input {
        File f
    }

    output {
        File f_out = f
    }
}
