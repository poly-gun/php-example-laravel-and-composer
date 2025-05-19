<?php

namespace Tests\Feature;

use Tests\TestCase;

class HelloTest extends TestCase
{
    public function test_can_hello(): void
    {
        $this->assertNotEmpty(config('services.hello.secret'));
    }
}
