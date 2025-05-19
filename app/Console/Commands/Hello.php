<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;

class Hello extends Command
{
    /**
     * The name and signature of the console command.
     *
     * @var string
     */
    protected $signature = 'hello';

    /**
     * The console command description.
     *
     * @var string
     */
    protected $description = 'Command description';

    /**
     * Execute the console command.
     */
    public function handle()
    {
        if (config('services.hello.secret')) {
            $this->info("Successful - Hello World");
        } else {
            $this->fail("Could not send a message due to missing TEST_SECRET_1");
        }
    }
}
